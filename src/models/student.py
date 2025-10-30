"""Modelos de dados para Estudantes."""

from datetime import UTC, date, datetime

from pydantic import BaseModel, Field, field_validator

__all__ = [
    "StudentModel",
    "StudentAddressDTO",
    "StudentContactDTO",
    "StudentCreateDTO",
    "StudentFirestoreDTO",
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
    active_until: date | None = None
    benefits: list[str] | None = Field(
        None, description="Lista de benefícios associados ao estudante."
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Data de criação do estudante.",
    )
    last_updated: datetime | None = Field(
        None, description="Data da última atualização do estudante."
    )


class StudentContactDTO(BaseModel):
    """DTO para informações de contato do estudante."""

    email: str | None = None
    phone: str | None = None


class StudentAddressDTO(BaseModel):
    """DTO para informações de endereço do estudante."""

    zip: str | None = None
    complement: str | None = None
    neighborhood: str | None = None


class StudentFirestoreDTO(BaseModel):
    """
    DTO do Aluno para leitura/escrita no Firestore.

    Esta estrutura espelha os documentos exportados em
    data/firestore_export/firestore_students.json.
    O ID do documento (ex.: "STD_I0L0M0O9_S1") é gerenciado externamente
    como doc_id no Firestore.
    """

    created_at: datetime
    updated_at: datetime
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

    @classmethod
    def from_create(
        cls, create_data: "StudentCreateDTO", tenant: str
    ) -> "StudentFirestoreDTO":
        """
        Cria um StudentFirestoreDTO a partir de StudentCreationDTO.

        Args:
            create_data: DTO com os dados de criação do aluno.
            tenant: ID do tenant ao qual o aluno pertence.

        Returns:
            Uma instância de StudentFirestoreDTO.
        """
        now = datetime.now(UTC)

        contact_dto = StudentContactDTO(
            email=create_data.email, phone=create_data.student_phone
        )
        address_dto = StudentAddressDTO(
            zip=create_data.zip,
            complement=create_data.add_complement,
            neighborhood=create_data.add_neighbor,
        )
        guardian_dto = (
            StudentGuardian(
                name=create_data.guardian_name,
                email=create_data.guardian_email,
                phone=create_data.guardian_phone,
            )
            if create_data.guardian_name
            else None
        )

        return cls(
            created_at=now,
            updated_at=now,
            occupation=create_data.student_occupation,
            tenant_id=tenant,
            contact=contact_dto,
            address=address_dto,
            guardian=guardian_dto,
            active_until=create_data.active_until,
            book=create_data.book,
            name=create_data.name,
        )

    def to_model(self, student_id: str) -> "StudentModel":
        """
        Converte o DTO do aluno para o modelo Student.
        """
        return StudentModel(
            id=student_id,
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
            active_until=self.active_until.date()
            if isinstance(self.active_until, datetime)
            else self.active_until,
        )

    @classmethod
    def from_student(cls, student: "StudentModel") -> "StudentFirestoreDTO":
        """
        Converte um objeto Student para um StudentFirestoreDTO.
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
            created_at=student.created_at,
            updated_at=student.last_updated
            if student.last_updated
            else datetime.now(UTC),
            occupation=student.student_occupation,
            tenant_id=student.tenant_id,
            contact=contact_dto,
            address=address_dto,
            guardian=guardian_dto,
            active_until=student.active_until,
            book=student.book,
            name=student.student_name,
        )


class StudentCreateDTO(BaseModel):
    """
    DTO para a criação de um novo estudante.

    Args:
        name: Nome do estudante.
        email: Email do estudante.
        tenant_id: ID do tenant ao qual o estudante pertence.
        book: Livro associado ao estudante.
        student_occupation: Ocupação do estudante.
        student_phone: Telefone do estudante.
        zip: Código postal do endereço do estudante.
        add_neighbor: Bairro do endereço do estudante.
        add_complement: Complemento do endereço do estudante.
        guardian_name: Nome do responsável do estudante.
        guardian_email: Email do responsável do estudante.
        guardian_phone: Telefone do responsável do estudante.
        active_until: Data de expiração da associação do estudante.
    """

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
