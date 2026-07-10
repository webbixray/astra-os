from uuid import UUID

from app.application.use_cases.ai.prompt_manager import PromptManager
from app.domain.entities.prompts import PromptCategory, PromptStatus, SystemPrompt


class ManagePromptsUseCase:
    def __init__(self, prompt_manager: PromptManager):
        self.prompt_manager = prompt_manager

    async def list_prompts(
        self,
        org_id: UUID | None = None,
        category: str | None = None,
    ) -> list[SystemPrompt]:
        repo = self.prompt_manager.repository
        if repo is None:
            return []
        if category:
            return await repo.list_by_category(category, org_id=org_id)
        return await repo.list_all(org_id=org_id)

    async def get_prompt(
        self,
        prompt_id: UUID,
    ) -> SystemPrompt | None:
        repo = self.prompt_manager.repository
        if repo is None:
            return None
        return await repo.find_by_id(prompt_id)

    async def create_prompt(
        self,
        name: str,
        content: str,
        category: PromptCategory = PromptCategory.SYSTEM,
        description: str = "",
        org_id: UUID | None = None,
        variables: list[str] | None = None,
        created_by: UUID | None = None,
    ) -> SystemPrompt:
        prompt = SystemPrompt.create(
            name=name,
            content=content,
            category=category,
            description=description,
            org_id=org_id,
            variables=variables,
            created_by=created_by,
        )
        return await self.prompt_manager.save_prompt(prompt)

    async def update_prompt(
        self,
        prompt_id: UUID,
        content: str | None = None,
        description: str | None = None,
        variables: list[str] | None = None,
        status: PromptStatus | None = None,
    ) -> SystemPrompt:
        repo = self.prompt_manager.repository
        if repo is None:
            raise RuntimeError("No repository configured")
        prompt = await repo.find_by_id(prompt_id)
        if prompt is None:
            raise ValueError(f"Prompt {prompt_id} not found")

        if content is not None and content != prompt.content:
            prompt.content = content
            prompt.bump_version()
        if description is not None:
            prompt.description = description
        if variables is not None:
            prompt.variables = variables
        if status is not None:
            prompt.status = status
            prompt.updated_at = prompt.updated_at

        return await repo.save(prompt)

    async def delete_prompt(self, prompt_id: UUID) -> None:
        repo = self.prompt_manager.repository
        if repo is None:
            return
        await repo.delete(prompt_id)
