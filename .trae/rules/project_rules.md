# Project Rules

1. Validate Python files linting with Ruff
2. Validate MD files linting with Markdownlint
3. Update reports in the docs/ folder
4. Update TODO.md
5. Do not use types Dict, List or Optional in Python scripts
6. Get dates from the system, do not use dates from the language model database

## Organization Rules

7. **Credentials Management**:
   - All credential files must be stored in `/credentials/` folder
   - Credential files must be added to `.gitignore`
   - Use environment variables in production
   - Document credential usage in `/credentials/README.md`

8. **Script Organization**:
   - Temporary scripts must be placed in `/scripts/temp/`
   - Use prefixes `temp_` or `*_temp.py` for truly temporary files
   - Organize scripts by category: development, maintenance, migration, testing
   - Document script purpose in file headers

9. **File Structure**:
   - Keep project root clean - avoid scattered utility files
   - Use appropriate folders: `/scripts/`, `/docs/`, `/src/`, `/tests/`
   - Configuration files can remain in root if they're framework-specific

## Operations Rules

10. **Bulk Operations**:

- Bulk operations (operações em massa) must NOT be executed automatically
- Bulk operations require explicit and specific user request
- Always confirm the scope and impact before executing bulk operations
- Document all bulk operations in execution logs
- Implement safeguards to prevent accidental bulk operations

## Business Rules

- For underage students, `nome_responsavel` (guardian name) must be filled
- Emails must follow valid format when filled
- ZIP code must follow Brazilian format (XXXXX-XXX) when filled
- Phone numbers must follow Brazilian format when filled
- The `curso` (course) field must correspond to courses offered by the school
