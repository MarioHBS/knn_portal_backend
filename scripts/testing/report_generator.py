#!/usr/bin/env python3
"""
Gerador de relatórios detalhados para testes de endpoints.

Este módulo gera relatórios em múltiplos formatos (HTML, JSON, TXT)
com métricas detalhadas de performance e cobertura dos testes.
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from test_runner import TestResult

logger = logging.getLogger(__name__)


@dataclass
class TestSummary:
    """Resumo estatístico dos testes."""

    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    success_rate: float
    total_time: float
    average_response_time: float
    fastest_response: float
    slowest_response: float
    endpoints_tested: int
    profiles_tested: list[str]


@dataclass
class ProfileSummary:
    """Resumo por perfil de usuário."""

    profile: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    success_rate: float
    average_response_time: float
    endpoints: list[str]


class ReportGenerator:
    """Gerador de relatórios de testes."""

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Templates HTML
        self.html_template = self._get_html_template()
        self.css_styles = self._get_css_styles()

    def generate_summary(self, results: list[TestResult]) -> TestSummary:
        """Gera resumo estatístico dos resultados."""
        if not results:
            return TestSummary(
                total_tests=0,
                passed_tests=0,
                failed_tests=0,
                skipped_tests=0,
                success_rate=0.0,
                total_time=0.0,
                average_response_time=0.0,
                fastest_response=0.0,
                slowest_response=0.0,
                endpoints_tested=0,
                profiles_tested=[],
            )

        total_tests = len(results)
        passed_tests = len([r for r in results if r.status == "pass"])
        failed_tests = len([r for r in results if r.status == "fail"])
        skipped_tests = len([r for r in results if r.status == "skip"])

        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0.0

        response_times = [r.response_time for r in results if r.response_time > 0]
        total_time = sum(response_times)
        average_response_time = (
            sum(response_times) / len(response_times) if response_times else 0.0
        )
        fastest_response = min(response_times) if response_times else 0.0
        slowest_response = max(response_times) if response_times else 0.0

        endpoints_tested = len({r.endpoint for r in results})
        profiles_tested = list(
            {r.endpoint.split(".")[0] for r in results if "." in r.endpoint}
        )

        return TestSummary(
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
            success_rate=success_rate,
            total_time=total_time,
            average_response_time=average_response_time,
            fastest_response=fastest_response,
            slowest_response=slowest_response,
            endpoints_tested=endpoints_tested,
            profiles_tested=profiles_tested,
        )

    def generate_profile_summaries(
        self, results: list[TestResult]
    ) -> list[ProfileSummary]:
        """Gera resumos por perfil de usuário."""
        profiles = {}

        for result in results:
            if "." not in result.endpoint:
                continue

            profile = result.endpoint.split(".")[0]

            if profile not in profiles:
                profiles[profile] = []

            profiles[profile].append(result)

        summaries = []

        for profile, profile_results in profiles.items():
            total_tests = len(profile_results)
            passed_tests = len([r for r in profile_results if r.status == "pass"])
            failed_tests = len([r for r in profile_results if r.status == "fail"])
            skipped_tests = len([r for r in profile_results if r.status == "skip"])

            success_rate = (
                (passed_tests / total_tests * 100) if total_tests > 0 else 0.0
            )

            response_times = [
                r.response_time for r in profile_results if r.response_time > 0
            ]
            average_response_time = (
                sum(response_times) / len(response_times) if response_times else 0.0
            )

            endpoints = list({r.endpoint for r in profile_results})

            summaries.append(
                ProfileSummary(
                    profile=profile,
                    total_tests=total_tests,
                    passed_tests=passed_tests,
                    failed_tests=failed_tests,
                    skipped_tests=skipped_tests,
                    success_rate=success_rate,
                    average_response_time=average_response_time,
                    endpoints=endpoints,
                )
            )

        return sorted(summaries, key=lambda x: x.profile)

    def generate_json_report(
        self,
        results: list[TestResult],
        summary: TestSummary,
        profile_summaries: list[ProfileSummary],
        filename: str | None = None,
    ) -> Path:
        """Gera relatório em formato JSON."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_report_{timestamp}.json"

        report_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "generator": "KNN Portal Test Suite",
                "version": "1.0.0",
            },
            "summary": asdict(summary),
            "profile_summaries": [asdict(ps) for ps in profile_summaries],
            "detailed_results": [
                {
                    "endpoint": r.endpoint,
                    "method": r.method,
                    "status": r.status,
                    "response_time": r.response_time,
                    "status_code": r.status_code,
                    "error_message": r.error_message,
                    "response_data": r.response_data,
                }
                for r in results
            ],
        }

        output_path = self.output_dir / filename

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Relatório JSON gerado: {output_path}")
        return output_path

    def generate_html_report(
        self,
        results: list[TestResult],
        summary: TestSummary,
        profile_summaries: list[ProfileSummary],
        filename: str | None = None,
    ) -> Path:
        """Gera relatório em formato HTML."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_report_{timestamp}.html"

        # Gerar conteúdo HTML
        html_content = self._generate_html_content(results, summary, profile_summaries)

        output_path = self.output_dir / filename

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"Relatório HTML gerado: {output_path}")
        return output_path

    def generate_txt_report(
        self,
        results: list[TestResult],
        summary: TestSummary,
        profile_summaries: list[ProfileSummary],
        filename: str | None = None,
    ) -> Path:
        """Gera relatório em formato texto."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_report_{timestamp}.txt"

        lines = []
        lines.append("=" * 80)
        lines.append("RELATÓRIO DE TESTES - PORTAL DE BENEFÍCIOS KNN")
        lines.append("=" * 80)
        lines.append(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        lines.append("")

        # Resumo geral
        lines.append("📊 RESUMO GERAL")
        lines.append("-" * 40)
        lines.append(f"Total de testes: {summary.total_tests}")
        lines.append(f"✅ Aprovados: {summary.passed_tests}")
        lines.append(f"❌ Falharam: {summary.failed_tests}")
        lines.append(f"⏭️ Ignorados: {summary.skipped_tests}")
        lines.append(f"📈 Taxa de sucesso: {summary.success_rate:.1f}%")
        lines.append(f"⏱️ Tempo total: {summary.total_time:.3f}s")
        lines.append(
            f"⚡ Tempo médio de resposta: {summary.average_response_time:.3f}s"
        )
        lines.append(f"🚀 Resposta mais rápida: {summary.fastest_response:.3f}s")
        lines.append(f"🐌 Resposta mais lenta: {summary.slowest_response:.3f}s")
        lines.append(f"🎯 Endpoints testados: {summary.endpoints_tested}")
        lines.append(f"👥 Perfis testados: {', '.join(summary.profiles_tested)}")
        lines.append("")

        # Resumo por perfil
        lines.append("👥 RESUMO POR PERFIL")
        lines.append("-" * 40)
        for ps in profile_summaries:
            lines.append(f"\n🔹 {ps.profile.upper()}")
            lines.append(
                f"   Total: {ps.total_tests} | Aprovados: {ps.passed_tests} | "
                f"Falharam: {ps.failed_tests} | Ignorados: {ps.skipped_tests}"
            )
            lines.append(f"   Taxa de sucesso: {ps.success_rate:.1f}%")
            lines.append(f"   Tempo médio: {ps.average_response_time:.3f}s")
            lines.append(f"   Endpoints: {len(ps.endpoints)}")

        lines.append("")

        # Resultados detalhados
        lines.append("📋 RESULTADOS DETALHADOS")
        lines.append("-" * 40)

        # Agrupar por perfil
        profiles = {}
        for result in results:
            if "." not in result.endpoint:
                profile = "outros"
            else:
                profile = result.endpoint.split(".")[0]

            if profile not in profiles:
                profiles[profile] = []
            profiles[profile].append(result)

        for profile, profile_results in sorted(profiles.items()):
            lines.append(f"\n🔹 {profile.upper()}")

            for result in profile_results:
                status_emoji = {"pass": "✅", "fail": "❌", "skip": "⏭️"}

                emoji = status_emoji.get(result.status, "❓")
                lines.append(
                    f"   {emoji} {result.endpoint} [{result.method}] - "
                    f"{result.status.upper()} ({result.response_time:.3f}s)"
                )

                if result.status_code:
                    lines.append(f"      HTTP {result.status_code}")

                if result.error_message:
                    lines.append(f"      Erro: {result.error_message}")

        lines.append("")
        lines.append("=" * 80)

        output_path = self.output_dir / filename

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        logger.info(f"Relatório TXT gerado: {output_path}")
        return output_path

    def generate_all_reports(self, results: list[TestResult]) -> dict[str, Path]:
        """Gera todos os formatos de relatório."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        summary = self.generate_summary(results)
        profile_summaries = self.generate_profile_summaries(results)

        reports = {
            "json": self.generate_json_report(
                results, summary, profile_summaries, f"test_report_{timestamp}.json"
            ),
            "html": self.generate_html_report(
                results, summary, profile_summaries, f"test_report_{timestamp}.html"
            ),
            "txt": self.generate_txt_report(
                results, summary, profile_summaries, f"test_report_{timestamp}.txt"
            ),
        }

        logger.info(f"Todos os relatórios gerados em: {self.output_dir}")
        return reports

    def _generate_html_content(
        self,
        results: list[TestResult],
        summary: TestSummary,
        profile_summaries: list[ProfileSummary],
    ) -> str:
        """Gera conteúdo HTML do relatório."""
        # Dados para gráficos
        profile_data = {
            "labels": [ps.profile for ps in profile_summaries],
            "passed": [ps.passed_tests for ps in profile_summaries],
            "failed": [ps.failed_tests for ps in profile_summaries],
            "skipped": [ps.skipped_tests for ps in profile_summaries],
        }

        # Tabela de resultados detalhados
        results_table = self._generate_results_table(results)

        # Substituir placeholders no template
        html_content = self.html_template.format(
            css_styles=self.css_styles,
            generated_at=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            total_tests=summary.total_tests,
            passed_tests=summary.passed_tests,
            failed_tests=summary.failed_tests,
            skipped_tests=summary.skipped_tests,
            success_rate=summary.success_rate,
            total_time=summary.total_time,
            average_response_time=summary.average_response_time,
            fastest_response=summary.fastest_response,
            slowest_response=summary.slowest_response,
            endpoints_tested=summary.endpoints_tested,
            profiles_tested=", ".join(summary.profiles_tested),
            profile_data_json=json.dumps(profile_data),
            profile_summaries_html=self._generate_profile_summaries_html(
                profile_summaries
            ),
            results_table=results_table,
        )

        return html_content

    def _generate_profile_summaries_html(
        self, profile_summaries: list[ProfileSummary]
    ) -> str:
        """Gera HTML para resumos por perfil."""
        html_parts = []

        for ps in profile_summaries:
            html_parts.append(f"""
            <div class="profile-card">
                <h3>🔹 {ps.profile.upper()}</h3>
                <div class="profile-stats">
                    <div class="stat">
                        <span class="stat-label">Total:</span>
                        <span class="stat-value">{ps.total_tests}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Aprovados:</span>
                        <span class="stat-value success">{ps.passed_tests}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Falharam:</span>
                        <span class="stat-value error">{ps.failed_tests}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Ignorados:</span>
                        <span class="stat-value warning">{ps.skipped_tests}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Taxa de Sucesso:</span>
                        <span class="stat-value">{ps.success_rate:.1f}%</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Tempo Médio:</span>
                        <span class="stat-value">{ps.average_response_time:.3f}s</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Endpoints:</span>
                        <span class="stat-value">{len(ps.endpoints)}</span>
                    </div>
                </div>
            </div>
            """)

        return "\n".join(html_parts)

    def _generate_results_table(self, results: list[TestResult]) -> str:
        """Gera tabela HTML com resultados detalhados."""
        rows = []

        for result in results:
            status_class = {"pass": "success", "fail": "error", "skip": "warning"}.get(
                result.status, ""
            )

            status_emoji = {"pass": "✅", "fail": "❌", "skip": "⏭️"}.get(
                result.status, "❓"
            )

            error_cell = result.error_message or "-"
            if len(error_cell) > 50:
                error_cell = error_cell[:47] + "..."

            rows.append(f"""
            <tr class="{status_class}">
                <td>{result.endpoint}</td>
                <td><span class="method">{result.method}</span></td>
                <td><span class="status-badge">{status_emoji} {result.status.upper()}</span></td>
                <td>{result.response_time:.3f}s</td>
                <td>{result.status_code or "-"}</td>
                <td title="{result.error_message or "-"}">{error_cell}</td>
            </tr>
            """)

        return "\n".join(rows)

    def _get_html_template(self) -> str:
        """Retorna template HTML."""
        return """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Testes - Portal KNN</title>
    <style>
        {css_styles}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Relatório de Testes</h1>
            <h2>Portal de Benefícios KNN</h2>
            <p class="generated-at">Gerado em: {generated_at}</p>
        </header>

        <section class="summary">
            <h2>📈 Resumo Geral</h2>
            <div class="summary-grid">
                <div class="summary-card">
                    <h3>Total de Testes</h3>
                    <div class="big-number">{total_tests}</div>
                </div>
                <div class="summary-card success">
                    <h3>✅ Aprovados</h3>
                    <div class="big-number">{passed_tests}</div>
                </div>
                <div class="summary-card error">
                    <h3>❌ Falharam</h3>
                    <div class="big-number">{failed_tests}</div>
                </div>
                <div class="summary-card warning">
                    <h3>⏭️ Ignorados</h3>
                    <div class="big-number">{skipped_tests}</div>
                </div>
                <div class="summary-card">
                    <h3>📈 Taxa de Sucesso</h3>
                    <div class="big-number">{success_rate:.1f}%</div>
                </div>
                <div class="summary-card">
                    <h3>⏱️ Tempo Total</h3>
                    <div class="big-number">{total_time:.3f}s</div>
                </div>
                <div class="summary-card">
                    <h3>⚡ Tempo Médio</h3>
                    <div class="big-number">{average_response_time:.3f}s</div>
                </div>
                <div class="summary-card">
                    <h3>🎯 Endpoints</h3>
                    <div class="big-number">{endpoints_tested}</div>
                </div>
            </div>
        </section>

        <section class="charts">
            <h2>📊 Gráficos</h2>
            <div class="chart-container">
                <canvas id="profileChart"></canvas>
            </div>
        </section>

        <section class="profiles">
            <h2>👥 Resumo por Perfil</h2>
            <div class="profiles-grid">
                {profile_summaries_html}
            </div>
        </section>

        <section class="results">
            <h2>📋 Resultados Detalhados</h2>
            <div class="table-container">
                <table class="results-table">
                    <thead>
                        <tr>
                            <th>Endpoint</th>
                            <th>Método</th>
                            <th>Status</th>
                            <th>Tempo</th>
                            <th>HTTP</th>
                            <th>Erro</th>
                        </tr>
                    </thead>
                    <tbody>
                        {results_table}
                    </tbody>
                </table>
            </div>
        </section>
    </div>

    <script>
        // Gráfico por perfil
        const ctx = document.getElementById('profileChart').getContext('2d');
        const profileData = {profile_data_json};

        new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: profileData.labels,
                datasets: [
                    {{
                        label: 'Aprovados',
                        data: profileData.passed,
                        backgroundColor: '#4CAF50'
                    }},
                    {{
                        label: 'Falharam',
                        data: profileData.failed,
                        backgroundColor: '#F44336'
                    }},
                    {{
                        label: 'Ignorados',
                        data: profileData.skipped,
                        backgroundColor: '#FF9800'
                    }}
                ]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Resultados por Perfil de Usuário'
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
        """

    def _get_css_styles(self) -> str:
        """Retorna estilos CSS."""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
        }

        header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        header h2 {
            font-size: 1.5em;
            font-weight: 300;
            margin-bottom: 10px;
        }

        .generated-at {
            opacity: 0.9;
            font-size: 0.9em;
        }

        section {
            background: white;
            margin-bottom: 30px;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        section h2 {
            margin-bottom: 20px;
            color: #333;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }

        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }

        .summary-card {
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            background: #f8f9fa;
            border-left: 4px solid #007bff;
        }

        .summary-card.success {
            border-left-color: #28a745;
        }

        .summary-card.error {
            border-left-color: #dc3545;
        }

        .summary-card.warning {
            border-left-color: #ffc107;
        }

        .summary-card h3 {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 10px;
        }

        .big-number {
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }

        .chart-container {
            position: relative;
            height: 400px;
            margin: 20px 0;
        }

        .profiles-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }

        .profile-card {
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 8px;
            background: #f8f9fa;
        }

        .profile-card h3 {
            margin-bottom: 15px;
            color: #333;
        }

        .profile-stats {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }

        .stat {
            display: flex;
            justify-content: space-between;
            padding: 5px 0;
        }

        .stat-label {
            color: #666;
        }

        .stat-value {
            font-weight: bold;
        }

        .stat-value.success {
            color: #28a745;
        }

        .stat-value.error {
            color: #dc3545;
        }

        .stat-value.warning {
            color: #ffc107;
        }

        .table-container {
            overflow-x: auto;
        }

        .results-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }

        .results-table th,
        .results-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }

        .results-table th {
            background-color: #f8f9fa;
            font-weight: 600;
            color: #333;
        }

        .results-table tr:hover {
            background-color: #f5f5f5;
        }

        .results-table tr.success {
            background-color: #d4edda;
        }

        .results-table tr.error {
            background-color: #f8d7da;
        }

        .results-table tr.warning {
            background-color: #fff3cd;
        }

        .method {
            background: #007bff;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
        }

        .status-badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
        }

        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }

            .summary-grid {
                grid-template-columns: 1fr;
            }

            .profiles-grid {
                grid-template-columns: 1fr;
            }

            .profile-stats {
                grid-template-columns: 1fr;
            }
        }
        """


def main():
    """Função principal para uso standalone."""
    import sys

    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Exemplo de uso
    generator = ReportGenerator()

    # Criar alguns resultados de exemplo
    example_results = [
        TestResult(
            endpoint="student.list_partners",
            method="GET",
            status="pass",
            response_time=0.245,
            status_code=200,
        ),
        TestResult(
            endpoint="student.get_partner_details",
            method="GET",
            status="skip",
            response_time=0.123,
            status_code=404,
            error_message="ID de teste não encontrado",
        ),
        TestResult(
            endpoint="admin.list_students",
            method="GET",
            status="pass",
            response_time=0.567,
            status_code=200,
        ),
    ]

    try:
        reports = generator.generate_all_reports(example_results)

        print("📊 Relatórios gerados:")
        for format_type, path in reports.items():
            print(f"   {format_type.upper()}: {path}")

        sys.exit(0)

    except Exception as e:
        logger.error(f"Erro ao gerar relatórios: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
