"""요청·응답 모델 공통 규칙. JSON 필드는 camelCase (예: user_id → userId)."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints
from pydantic.alias_generators import to_camel

# 빈칸·공백만 있으면 422 VALIDATION_ERROR (fieldErrors code=REQUIRED)
Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
