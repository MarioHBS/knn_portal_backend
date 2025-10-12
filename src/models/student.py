"""Modelos de dados para Estudantes."""

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from src.utils.id_generators import IDGenerators

__all__ = [
    "StudentModel",
    "StudentAddressDTO",
    "StudentContactDTO",
    "StudentCreationDTO",
    "StudentDTO",
    "StudentGuardian",
]


class StudentGuardian(BaseModel):
    """Modelo do Responsável do aluno, quando necessário"""

    phone: str | None = None
    email: str | None = None
    name: str | None = None


class StudentModel(BaseModel):
    """Modelo para alunos."""

    id: str = Field(default="")
    tenant_id: str
    student_name: str
    book: str
    student_occupation: str | None = None
    student_email: str | None = None
    student_phone: str | None = None
    zip: str | None = None
    add_neighbor: str | None = None
    add_complement: str | None = None
    guardian: StudentGuardian | None = None
    active_until: date

    def __init__(self, **data):
        super().__init__(**data)
        if not self.id:
            self.id = IDGenerators.gerar_id_aluno(
                nome=self.student_name,
                curso=self.book,
                cep=self.zip or "",
                celular=self.student_phone or self.guardian.phone
                if self.guardian
                else "",
                email=self.student_email or self.guardian.email
                if self.guardian
                else "",
            )

    class Config:
        from_attributes = True


# DTOs de Aluno para Firestore
class StudentContactDTO(BaseModel):
    """Subdocumento de contato do aluno (Firestore)."""

    email: str | None = None
    phone: str | None = None


class StudentAddressDTO(BaseModel):
    """Subdocumento de endereço do aluno (Firestore)."""

    zip: str | None = None
    complement: str | None = None
    neighborhood: str | None = None


class StudentDTO(BaseModel):
    """
    DTO do Aluno para leitura/escrita no Firestore.

    Esta estrutura espelha os documentos exportados em
    data/firestore_export/firestore_students.json.
    O ID do documento (ex.: "STD_I0L0M0O9_S1") é gerenciado externamente
    como doc_id no Firestore.
    """

    created_at: datetime | None = None
    updated_at: datetime | None = None
    occupation: str | None = None
    tenant_id: str
    contact: StudentContactDTO | None = None
    address: StudentAddressDTO | None = None
    guardian: StudentGuardian | None = None
    active_until: datetime
    book: str | None = None
    name: str

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
        }

    def to_student(self) -> "StudentModel":
        """
        Converte o DTO do aluno para o modelo Student.
        """
        return StudentModel(
            id="",  # Será gerado automaticamente pelo construtor de Student
            tenant_id=self.tenant_id,
            student_name=self.name,
            book=self.book or "CURSO_PADRAO",  # TODO: Mapear o curso real
            student_occupation=self.occupation,
            student_email=self.contact.email if self.contact else None,
            student_phone=self.contact.phone if self.contact else None,
            zip=self.address.zip if self.address else None,
            add_neighbor=self.address.neighborhood if self.address else None,
            add_complement=self.address.complement if self.address else None,
            guardian=StudentGuardian(
                name=self.guardian.name,
                email=self.guardian.email,
                phone=self.guardian.phone,
            )
            if self.guardian
            else None,
            active_until=self.active_until,
        )

    @classmethod
    def from_student(cls, student: "StudentModel") -> "StudentDTO":
        """
        Converte um objeto Student para um StudentDTO.
        """
        contact_dto = StudentContactDTO(
            email=student.student_email, phone=student.student_phone
        )
        address_dto = StudentAddressDTO(
            zip=student.zip,
            complement=student.add_complement,
            neighborhood=student.add_neighbor,
        )
        guardian_dto = (
            StudentGuardian(
                phone=student.guardian.phone,
                email=student.guardian.email,
                name=student.guardian.name,
            )
            if student.guardian
            else None
        )

        return cls(
            created_at=datetime.now(),  # Ou a data de criação real se disponível
            updated_at=datetime.now(),  # Ou a data de atualização real se disponível
            occupation=student.student_occupation,
            tenant_id=student.tenant_id,
            contact=contact_dto,
            address=address_dto,
            guardian=guardian_dto,
            active_until=student.active_until,
            book=student.book,
            name=student.student_name,
        )


class StudentCreationDTO(BaseModel):
    """DTO para a criação de um novo estudante."""

    name: str
    email: str
    tenant_id: str
    book: str
    student_occupation: str | None = None
    student_phone: str | None = None
    zip: str | None = None
    add_neighbor: str | None = None
    add_complement: str | None = None
    guardian_name: str | None = None
    guardian_email: str | None = None
    guardian_phone: str | None = None
    active_until: date

    @field_validator("email")
    def email_must_be_valid(cls, v):  # noqa: N805
        if v and "@" not in v:
            raise ValueError("Email inválido")
        return v


class StudentUpdateDTO(BaseModel):
    """DTO para atualização de um estudante existente."""

    name: str | None = None
    email: str | None = None
    tenant_id: str | None = None
    book: str | None = None
    student_occupation: str | None = None
    student_phone: str | None = None
    zip: str | None = None
    add_neighbor: str | None = None
    add_complement: str | None = None
    guardian_name: str | None = None
    guardian_email: str | None = None
    guardian_phone: str | None = None
    active_until: date | None = None
