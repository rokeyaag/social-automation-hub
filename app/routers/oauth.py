from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import encrypt_token
from app.models.user import User
from app.models.social_account import SocialAccount
from app.schemas.social import SocialAccountOut, FacebookManualConnectRequest
from app.services.auth_service import get_current_user
from app.services.facebook_service import FacebookService
from app.services.linkedin_service import LinkedInService

router = APIRouter(prefix="/api/v1/oauth", tags=["Social Accounts & OAuth"])

@router.get("/accounts", response_model=List[SocialAccountOut])
def list_connected_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all social accounts connected by the current user."""
    return db.query(SocialAccount).filter(SocialAccount.user_id == current_user.id).all()

# --- Facebook OAuth ---
@router.get("/facebook/connect")
def connect_facebook(current_user: User = Depends(get_current_user)):
    """Initiates Facebook OAuth flow."""
    auth_url = FacebookService.get_authorization_url(state=str(current_user.id))
    return RedirectResponse(url=auth_url)

@router.get("/facebook/callback")
@router.get("/facebook/simulate-callback")
def facebook_callback(
    code: str = Query(default="sim_code"),
    state: str = Query(default="1"),
    db: Session = Depends(get_db)
):
    """Handles OAuth callback and stores encrypted page access token."""
    user_id = int(state)
    token_data = FacebookService.exchange_code_for_token(code)

    # Check if this account was already connected by this user
    existing = db.query(SocialAccount).filter(
        SocialAccount.user_id == user_id,
        SocialAccount.platform == "facebook",
        SocialAccount.platform_account_id == token_data["platform_account_id"]
    ).first()

    if existing:
        existing.account_name = token_data["account_name"]
        existing.encrypted_access_token = encrypt_token(token_data["access_token"])
    else:
        new_account = SocialAccount(
            user_id=user_id,
            platform="facebook",
            platform_account_id=token_data["platform_account_id"],
            account_name=token_data["account_name"],
            account_type=token_data["account_type"],
            encrypted_access_token=encrypt_token(token_data["access_token"])
        )
        db.add(new_account)

    db.commit()
    return RedirectResponse(url="/accounts?connected=facebook", status_code=303)

@router.post("/facebook/manual-connect")
def manual_connect_facebook(
    payload: FacebookManualConnectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Verifies and stores a real Facebook Page ID and Page Access Token."""
    if not payload.page_id.strip() or not payload.access_token.strip():
        raise HTTPException(status_code=400, detail="Facebook Page ID and Page Access Token are both required.")

    # Validate with Meta Graph API
    verify_result = FacebookService.verify_page_token(
        page_id=payload.page_id.strip(),
        access_token=payload.access_token.strip()
    )

    if not verify_result.get("valid"):
        raise HTTPException(
            status_code=400,
            detail=verify_result.get("error", "Invalid Page ID or Access Token. Meta API rejected these credentials.")
        )

    verified_page_id = str(verify_result.get("page_id", payload.page_id.strip()))
    verified_name = verify_result.get("page_name") or payload.page_name or "Facebook Page"

    # Upsert account for this user
    existing = db.query(SocialAccount).filter(
        SocialAccount.user_id == current_user.id,
        SocialAccount.platform == "facebook"
    ).first()

    if existing:
        existing.platform_account_id = verified_page_id
        existing.account_name = verified_name
        existing.account_type = "page"
        existing.encrypted_access_token = encrypt_token(payload.access_token.strip())
    else:
        new_account = SocialAccount(
            user_id=current_user.id,
            platform="facebook",
            platform_account_id=verified_page_id,
            account_name=verified_name,
            account_type="page",
            encrypted_access_token=encrypt_token(payload.access_token.strip())
        )
        db.add(new_account)

    db.commit()
    return {
        "success": True,
        "message": f"Successfully connected Facebook Page: '{verified_name}' (ID: {verified_page_id})!",
        "page_id": verified_page_id,
        "page_name": verified_name
    }

# --- LinkedIn OAuth ---
@router.get("/linkedin/connect")
def connect_linkedin(current_user: User = Depends(get_current_user)):
    """Initiates LinkedIn OAuth flow."""
    auth_url = LinkedInService.get_authorization_url(state=str(current_user.id))
    return RedirectResponse(url=auth_url)

@router.get("/linkedin/callback")
@router.get("/linkedin/simulate-callback")
def linkedin_callback(
    code: str = Query(default="sim_code"),
    state: str = Query(default="1"),
    db: Session = Depends(get_db)
):
    """Handles LinkedIn OAuth callback and stores encrypted access token."""
    user_id = int(state)
    token_data = LinkedInService.exchange_code_for_token(code)

    existing = db.query(SocialAccount).filter(
        SocialAccount.user_id == user_id,
        SocialAccount.platform == "linkedin",
        SocialAccount.platform_account_id == token_data["platform_account_id"]
    ).first()

    if existing:
        existing.account_name = token_data["account_name"]
        existing.encrypted_access_token = encrypt_token(token_data["access_token"])
    else:
        new_account = SocialAccount(
            user_id=user_id,
            platform="linkedin",
            platform_account_id=token_data["platform_account_id"],
            account_name=token_data["account_name"],
            account_type=token_data["account_type"],
            encrypted_access_token=encrypt_token(token_data["access_token"])
        )
        db.add(new_account)

    db.commit()
    return RedirectResponse(url="/accounts?connected=linkedin", status_code=303)

# --- Disconnect Account ---
@router.delete("/accounts/{account_id}")
def disconnect_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Disconnects and removes a social account for the current user."""
    account = db.query(SocialAccount).filter(
        SocialAccount.id == account_id,
        SocialAccount.user_id == current_user.id
    ).first()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found.")

    db.delete(account)
    db.commit()
    return {"message": "Account disconnected successfully."}
