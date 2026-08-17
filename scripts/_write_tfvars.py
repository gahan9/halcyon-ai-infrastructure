from pathlib import Path

Path(r"C:\Projects\halcyon-ai-infrastructure\infra\terraform\environments\staging\staging.tfvars").write_text(
    "\n".join(
        [
            'project_name              = "halcyon-part1-staging"',
            'region                    = "nyc3"',
            'vpc_ip_range              = "10.20.0.0/24"',
            'postgres_version          = "16"',
            'postgres_size             = "db-s-1vcpu-1gb"',
            "postgres_storage_size_mib = 10240",
            'valkey_version            = "8"',
            'valkey_size               = "db-s-1vcpu-1gb"',
            'spaces_bucket_name        = "halcyon-part1-stg-202608161050"',
            "spaces_force_destroy      = true",
            'registry_name             = "halcyonstg202608161050"',
            'registry_subscription_tier_slug = "starter"',
            "",
        ]
    ),
    encoding="utf-8",
    newline="\n",
)
print("tfvars written")
