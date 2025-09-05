#!/usr/bin/env python3
"""Script para configurar o agendamento automático da limpeza de códigos expirados.

Este script configura o Windows Task Scheduler para executar a limpeza
automática de códigos de validação expirados a cada 5 minutos.

Uso:
    python scripts/maintenance/setup_cleanup_scheduler.py

Requisitos:
    - Windows com Task Scheduler
    - Permissões administrativas
    - Python instalado no sistema
"""

import os
import sys
from pathlib import Path


def create_task_scheduler_xml():
    """Cria o arquivo XML de configuração para o Task Scheduler."""

    # Obter caminhos absolutos
    project_root = Path(__file__).parent.parent.parent
    python_exe = sys.executable
    script_path = project_root / "scripts" / "maintenance" / "cleanup_expired_codes.py"

    xml_content = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>2024-01-01T00:00:00</Date>
    <Author>KNN Portal Journey Club</Author>
    <Description>Limpeza automática de códigos de validação expirados</Description>
  </RegistrationInfo>
  <Triggers>
    <TimeTrigger>
      <Repetition>
        <Interval>PT5M</Interval>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
      <StartBoundary>2024-01-01T00:00:00</StartBoundary>
      <Enabled>true</Enabled>
    </TimeTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT10M</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{python_exe}</Command>
      <Arguments>"{script_path}"</Arguments>
      <WorkingDirectory>{project_root}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>"""

    return xml_content


def setup_windows_task_scheduler():
    """Configura o Windows Task Scheduler para executar a limpeza automática."""
    try:
        # Criar arquivo XML temporário
        xml_content = create_task_scheduler_xml()
        temp_xml_path = Path.cwd() / "temp_cleanup_task.xml"

        with open(temp_xml_path, "w", encoding="utf-16") as f:
            f.write(xml_content)

        # Comando para criar a tarefa no Task Scheduler
        task_name = "KNN_ValidationCodes_Cleanup"
        cmd = f'schtasks /create /tn "{task_name}" /xml "{temp_xml_path}" /f'

        print(f"Criando tarefa no Task Scheduler: {task_name}")
        print(f"Comando: {cmd}")

        # Executar comando
        result = os.system(cmd)

        # Remover arquivo temporário
        temp_xml_path.unlink()

        if result == 0:
            print("✅ Tarefa criada com sucesso!")
            print("A limpeza automática será executada a cada 5 minutos.")
            print(f'Para verificar: schtasks /query /tn "{task_name}"')
            print(f'Para desabilitar: schtasks /change /tn "{task_name}" /disable')
            print(f'Para remover: schtasks /delete /tn "{task_name}" /f')
        else:
            print(
                "❌ Erro ao criar tarefa. Verifique se você tem permissões administrativas."
            )
            return False

        return True

    except Exception as e:
        print(f"❌ Erro ao configurar Task Scheduler: {e}")
        return False


def create_systemd_service():
    """Cria arquivo de serviço systemd para sistemas Linux (informativo)."""

    project_root = Path(__file__).parent.parent.parent
    python_exe = sys.executable
    script_path = project_root / "scripts" / "maintenance" / "cleanup_expired_codes.py"

    service_content = f"""[Unit]
Description=KNN Portal Journey Club - Limpeza de Códigos de Validação
After=network.target

[Service]
Type=oneshot
User=www-data
WorkingDirectory={project_root}
ExecStart={python_exe} {script_path}
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""

    timer_content = """[Unit]
Description=Executar limpeza de códigos a cada 5 minutos
Requires=knn-cleanup-codes.service

[Timer]
OnCalendar=*:0/5
Persistent=true

[Install]
WantedBy=timers.target
"""

    print("\n=== Configuração para Linux (systemd) ===")
    print("Para sistemas Linux, crie os seguintes arquivos:")
    print("\n1. /etc/systemd/system/knn-cleanup-codes.service:")
    print(service_content)
    print("\n2. /etc/systemd/system/knn-cleanup-codes.timer:")
    print(timer_content)
    print("\n3. Execute os comandos:")
    print("   sudo systemctl daemon-reload")
    print("   sudo systemctl enable knn-cleanup-codes.timer")
    print("   sudo systemctl start knn-cleanup-codes.timer")


def main():
    """Função principal do script de configuração."""
    print("=== Configuração do Agendamento de Limpeza Automática ===")
    print(
        "Este script configura a execução automática da limpeza de códigos expirados.\n"
    )

    # Verificar sistema operacional
    if os.name == "nt":  # Windows
        print("Sistema detectado: Windows")
        print("Configurando Windows Task Scheduler...\n")

        success = setup_windows_task_scheduler()

        if success:
            print("\n✅ Configuração concluída com sucesso!")
            print(
                "A limpeza automática está agora configurada para executar a cada 5 minutos."
            )
        else:
            print(
                "\n❌ Falha na configuração. Verifique as permissões e tente novamente."
            )

    else:  # Linux/Unix
        print("Sistema detectado: Linux/Unix")
        create_systemd_service()

    print("\n=== Execução Manual ===")
    print("Para executar a limpeza manualmente:")
    print(f"python {Path(__file__).parent / 'cleanup_expired_codes.py'}")


if __name__ == "__main__":
    main()
