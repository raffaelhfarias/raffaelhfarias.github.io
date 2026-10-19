import json
import sys
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings
from app.db import Membership, SessionLocal, Tenant, User
from app.security import hash_password


def main():
    cfg = settings()
    db = SessionLocal()
    try:
        users = {
            "owner_a": ("owner.a@example.test", cfg.demo_owner_password),
            "owner_b": ("owner.b@example.test", cfg.demo_second_owner_password),
            "viewer_a": ("viewer.a@example.test", cfg.demo_viewer_password),
        }
        identities = {}
        for key, (email, password) in users.items():
            user = db.scalar(select(User).where(User.email == email))
            if not user:
                user = User(email=email, password_hash=hash_password(password))
                db.add(user)
            identities[key] = user
        db.flush()
        tenant_names = {"tenant_a": "Demo Alpha", "tenant_b": "Demo Beta"}
        tenants = {}
        for key, name in tenant_names.items():
            tenant = db.scalar(select(Tenant).where(Tenant.name == name))
            if not tenant:
                tenant = Tenant(name=name)
                db.add(tenant)
                db.flush()
            tenants[key] = tenant
        desired = {
            (tenants["tenant_a"].id, identities["owner_a"].id): "owner",
            (tenants["tenant_b"].id, identities["owner_b"].id): "owner",
            (tenants["tenant_a"].id, identities["viewer_a"].id): "viewer",
        }
        demo_user_ids = {user.id for user in identities.values()}
        for membership in db.scalars(select(Membership)).all():
            if (
                membership.user_id in demo_user_ids
                and (membership.tenant_id, membership.user_id) not in desired
            ):
                db.delete(membership)
        db.flush()
        for (tenant_id, user_id), role in desired.items():
            membership = db.get(Membership, (tenant_id, user_id))
            if membership:
                membership.role = role
            else:
                db.add(Membership(tenant_id=tenant_id, user_id=user_id, role=role))
        db.commit()
        print(
            json.dumps(
                [
                    {
                        "id": identities["owner_a"].id,
                        "email": identities["owner_a"].email,
                        "role": "owner",
                    },
                    {
                        "id": identities["owner_b"].id,
                        "email": identities["owner_b"].email,
                        "role": "owner",
                    },
                    {
                        "id": identities["viewer_a"].id,
                        "email": identities["viewer_a"].email,
                        "role": "viewer",
                    },
                ],
                sort_keys=True,
            )
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
