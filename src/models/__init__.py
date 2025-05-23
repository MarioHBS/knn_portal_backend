"""
Modelos de dados para o Portal de Benefícios KNN.
"""
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator
import uuid

# Modelos base
class BaseResponse(BaseModel):
    """Modelo base para respostas da API."""
    msg: str = "ok"

class ErrorResponse(BaseModel):
    """Modelo para respostas de erro."""
    error: dict

# Modelos de entidades
class Student(BaseModel):
    """Modelo para alunos."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    cpf_hash: str
    name: str
    email: str
    course: str
    active_until: date
    
    class Config:
        orm_mode = True

class Partner(BaseModel):
    """Modelo para parceiros."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    trade_name: str
    category: str
    address: str
    active: bool = True
    
    class Config:
        orm_mode = True

class Promotion(BaseModel):
    """Modelo para promoções."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    partner_id: str
    title: str
    type: str
    valid_from: datetime
    valid_to: datetime
    active: bool = True
    
    class Config:
        orm_mode = True

class ValidationCode(BaseModel):
    """Modelo para códigos de validação."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    student_id: str
    partner_id: str
    code_hash: str
    expires: datetime
    used_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class Redemption(BaseModel):
    """Modelo para resgates."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    validation_code_id: str
    value: float
    used_at: datetime
    
    class Config:
        orm_mode = True

# Modelos para requisições
class ValidationCodeRequest(BaseModel):
    """Modelo para requisição de código de validação."""
    partner_id: str

class RedeemRequest(BaseModel):
    """Modelo para requisição de resgate de código."""
    code: str
    cpf: str
    
    @validator('code')
    def validate_code(cls, v):
        if not v.isdigit() or len(v) != 6:
            raise ValueError('Código deve conter 6 dígitos numéricos')
        return v
    
    @validator('cpf')
    def validate_cpf(cls, v):
        if not v.isdigit() or len(v) != 11:
            raise ValueError('CPF deve conter 11 dígitos numéricos')
        return v

class PromotionRequest(BaseModel):
    """Modelo para requisição de criação/atualização de promoção."""
    title: str
    type: str
    valid_from: datetime
    valid_to: datetime
    active: bool = True

class NotificationRequest(BaseModel):
    """Modelo para requisição de envio de notificações."""
    target: str
    filter: dict = {}
    message: str
    type: str = "both"
    
    @validator('target')
    def validate_target(cls, v):
        if v not in ["students", "partners"]:
            raise ValueError('Target deve ser "students" ou "partners"')
        return v
    
    @validator('type')
    def validate_type(cls, v):
        if v not in ["email", "push", "both"]:
            raise ValueError('Type deve ser "email", "push" ou "both"')
        return v

# Modelos para respostas
class PartnerDetail(Partner):
    """Modelo para detalhes de parceiro com promoções."""
    promotions: List[Promotion] = []

class PartnerListResponse(BaseResponse):
    """Modelo para resposta de listagem de parceiros."""
    data: dict

class PartnerDetailResponse(BaseResponse):
    """Modelo para resposta de detalhes de parceiro."""
    data: PartnerDetail

class ValidationCodeResponse(BaseResponse):
    """Modelo para resposta de geração de código de validação."""
    data: dict

class RedeemResponse(BaseResponse):
    """Modelo para resposta de resgate de código."""
    data: dict

class PromotionResponse(BaseResponse):
    """Modelo para resposta de criação/atualização de promoção."""
    data: Promotion

class PromotionListResponse(BaseResponse):
    """Modelo para resposta de listagem de promoções."""
    data: dict

class ReportResponse(BaseResponse):
    """Modelo para resposta de relatório."""
    data: dict

class MetricsResponse(BaseResponse):
    """Modelo para resposta de métricas."""
    data: dict

class NotificationResponse(BaseResponse):
    """Modelo para resposta de envio de notificações."""
    data: dict

class HistoryResponse(BaseResponse):
    """Modelo para resposta de histórico de resgates."""
    data: dict

class FavoritesResponse(BaseResponse):
    """Modelo para resposta de favoritos."""
    data: List[Partner]

class EntityResponse(BaseModel):
    """Modelo para resposta de entidade."""
    data: dict

class EntityListResponse(BaseResponse):
    """Modelo para resposta de listagem de entidades."""
    data: dict
