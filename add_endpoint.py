import subprocess, os
os.chdir("/Users/neominnthu/Desktop/Project/agency")

# Read the file
with open("apps/api/app/presentation/routes/campaigns/campaign_routes.py", "r") as f:
    content = f.read()

# Find the last "from None" and add our endpoint after it
endpoint = '''

@router.post(
    "/campaigns/sample",
    status_code=status.HTTP_201_CREATED,
    summary="Create sample campaigns for onboarding",
)
async def create_sample_campaigns(
    organization_id: UUID,
    count: int = Query(default=3, ge=1, le=5),
    user_id: UUID = Depends(require_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create sample campaigns for new user onboarding."""
    await require_org_role(organization_id, "member", user_id, db)

    repo = CampaignRepositoryImpl(db)
    use_case = CreateCampaignUseCase(repo)

    sample_campaigns = [
        {
            "name": "Brand Awareness Launch",
            "objective": CampaignObjective.BRAND_AWARENESS,
            "description": "Launch campaign to introduce your brand to new audiences",
            "target_audience": {"interests": ["technology", "innovation"], "age_range": "25-45"},
            "budget": 5000.0,
        },
        {
            "name": "Lead Generation Campaign",
            "objective": CampaignObjective.LEAD_GENERATION,
            "description": "Generate qualified leads through targeted content",
            "target_audience": {"job_titles": ["CTO", "VP Engineering", "Director"], "company_size": "50-500"},
            "budget": 3000.0,
        },
        {
            "name": "Product Launch Campaign",
            "objective": CampaignObjective.CONVERSIONS,
            "description": "Drive conversions for new product launch",
            "target_audience": {"interests": ["saas", "productivity"], "intent": "high"},
            "budget": 4000.0,
        },
        {
            "name": "Retargeting Campaign",
            "objective": CampaignObjective.CONVERSIONS,
            "description": "Retarget website visitors with personalized offers",
            "target_audience": {"website_visitors": 30, "engaged_users": True},
            "budget": 2000.0,
        },
        {
            "name": "Thought Leadership Content",
            "objective": CampaignObjective.BRAND_AWARENESS,
            "description": "Establish brand authority through educational content",
            "target_audience": {"interests": ["leadership", "strategy"], "seniority": "director+"},
            "budget": 1500.0,
        },
    ]

    created = []
    for i in range(min(count, len(sample_campaigns))):
        sc = sample_campaigns[i]
        campaign = await use_case.execute(
            organization_id=organization_id,
            name=sc["name"],
            objective=sc["objective"],
            target_audience=sc["target_audience"],
            budget=sc["budget"],
            created_by=user_id,
            description=sc.get("description"),
        )
        created.append({
            "id": str(campaign.id),
            "name": campaign.name,
            "objective": campaign.objective.value,
            "budget": campaign.budget,
        })

    return {
        "message": f"Created {len(created)} sample campaigns",
        "campaigns": created,
    }
'''

# Find the last "from None" and add after it
last_from_none = content.rfind("from None")
if last_from_none != -1:
    # Find the end of that line
    end_of_line = content.find("\n", last_from_none)
    if end_of_line == -1:
        end_of_line = len(content)
    new_content = content[:end_of_line+1] + endpoint
    with open("apps/api/app/presentation/routes/campaigns/campaign_routes.py", "w") as f:
        f.write(new_content)
    print("Added endpoint successfully")
else:
    print("Could not find 'from None'")

print("Done")