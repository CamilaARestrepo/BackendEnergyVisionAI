# -*- coding: utf-8 -*-
"""Generate architecture diagrams as PNG for EnergyVision AI thesis."""
import os
import sys
import io

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np

OUTPUT_DIR = r"C:\Users\cacevedo\Desktop\ProyectoTrabajodeGrado\resiudossolidos"

# Brand colors
EMERALD = "#059669"
BLUE = "#2563eb"
AMBER = "#d97706"
PINK = "#db2777"
PURPLE = "#7c3aed"
SLATE = "#475569"
RED = "#ef4444"
LIGHT_GREEN = "#d1fae5"
LIGHT_BLUE = "#dbeafe"
LIGHT_AMBER = "#fef3c7"
LIGHT_PINK = "#fce7f3"
LIGHT_PURPLE = "#f5f0ff"
DARK_BG = "#0f172a"
GRAY = "#64748b"


def draw_box(ax, x, y, w, h, text, face_color, text_color="black", fontsize=9,
             fontweight="normal", edge_color=None, alpha=0.9, lw=1.5):
    if edge_color is None:
        edge_color = face_color
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                         facecolor=face_color, edgecolor=edge_color,
                         linewidth=lw, alpha=alpha)
    ax.add_patch(box)
    lines = text.split('\n')
    total_h = len(lines) * (fontsize + 2)
    start_y = y + h / 2 + total_h / 2 - fontsize - 1
    for i, line in enumerate(lines):
        ly = start_y - i * (fontsize + 3)
        ax.text(x + w / 2, ly, line, ha="center", va="center",
                fontsize=fontsize, fontweight=fontweight, color=text_color,
                family="sans-serif")


def draw_arrow(ax, x1, y1, x2, y2, color=GRAY, lw=1.5):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color=color, lw=lw))


def draw_layer(ax, x, y, w, h, title, border_color):
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2",
                         facecolor=border_color, edgecolor=border_color,
                         linewidth=2, alpha=0.12)
    ax.add_patch(box)
    tb = FancyBboxPatch((x, y + h - 0.8), w, 0.8, boxstyle="round,pad=0.1",
                        facecolor=border_color, edgecolor=border_color,
                        linewidth=0, alpha=0.85)
    ax.add_patch(tb)
    ax.text(x + w / 2, y + h - 0.4, title, ha="center", va="center",
            fontsize=9, fontweight="bold", color="white", family="sans-serif")


def diagram_1_alto_nivel(filepath):
    fig, ax = plt.subplots(figsize=(16, 10))
    ax.set_xlim(0, 16); ax.set_ylim(0, 10); ax.axis("off")
    ax.set_facecolor(DARK_BG); fig.patch.set_facecolor(DARK_BG)

    ax.text(8, 9.5, "EnergyVision AI -- Arquitectura de Alto Nivel",
            ha="center", fontsize=16, fontweight="bold", color=EMERALD)

    draw_box(ax, 4, 8.2, 8, 0.7, "Navegador (Cliente SPA)\nReact 19 + Vite | puerto 5173",
             LIGHT_GREEN, text_color="#064e3b", fontsize=10, edge_color=EMERALD)
    draw_arrow(ax, 8, 8.2, 8, 7.1, GRAY)

    draw_box(ax, 1, 6.2, 14, 0.9,
             "Frontend -- React 19 + Vite + Tailwind CSS 4 + Base UI (shadcn)\nDashboard / History / Settings | Zustand + TanStack Query + Sonner + Axios",
             LIGHT_BLUE, text_color="#1e3a5f", fontsize=9, edge_color=BLUE)
    draw_arrow(ax, 8, 6.2, 8, 5.4, GRAY)

    draw_box(ax, 0.5, 4.3, 15, 1.1,
             "Backend -- FastAPI + Uvicorn (puerto 8000)\nPOST /scan | GET /objects | PUT /settings | GET /export | /uploads/{file}\nPipeline LangGraph: validate -> detection -> waste -> energy -> enrichment -> persist",
             LIGHT_AMBER, text_color="#78350f", fontsize=9, edge_color=AMBER)
    draw_arrow(ax, 8, 4.3, 8, 3.5, GRAY)

    draw_box(ax, 2, 2.3, 12, 1.2,
             "Capa de Datos -- ./data/\nSQLite (energyvision.db) | uploads/ (imagenes) | secret.key (Fernet AES-128)\nTablas: detected_objects | energy_data | ai_settings",
             LIGHT_PINK, text_color="#831843", fontsize=9, edge_color=PINK)

    ax.text(13.5, 5.0, "APIs IA", ha="center", fontsize=8, fontweight="bold", color=PURPLE)
    providers = [("OpenAI\ngpt-4o",), ("Anthropic\nClaude",), ("Google\nGemini",), ("Ollama\n(Local)",)]
    for i, (name,) in enumerate(providers):
        py = 6.6 - i * 0.55
        draw_box(ax, 12, py, 3, 0.45, name, LIGHT_PURPLE, text_color="#4c1d95",
                 fontsize=7, edge_color=PURPLE, lw=1)
    ax.plot([13.5, 12], [5.5, 6.2], color=PURPLE, lw=0.8, linestyle="--", alpha=0.5)

    fig.savefig(filepath, dpi=180, bbox_inches="tight", facecolor=DARK_BG)
    plt.close(fig)
    print(f"  OK {os.path.basename(filepath)}")


def diagram_2_arquitectura_logica(filepath):
    fig, ax = plt.subplots(figsize=(18, 13))
    ax.set_xlim(0, 18); ax.set_ylim(0, 13); ax.axis("off")
    ax.set_facecolor(DARK_BG); fig.patch.set_facecolor(DARK_BG)
    ax.text(9, 12.6, "EnergyVision AI -- Arquitectura Logica (Clean Architecture)",
            ha="center", fontsize=15, fontweight="bold", color=EMERALD)

    # Presentation
    draw_layer(ax, 0.5, 9.2, 17, 3.2, "CAPA DE PRESENTACION (React 19 + Vite + Base UI)", EMERALD)
    pres = [
        (0.8, 11.8, 3.0, "Dashboard.tsx\nScanner Multimodal"),
        (4.1, 11.8, 3.0, "History.tsx\nRegistro LER"),
        (7.4, 11.8, 3.0, "SettingsPage.tsx\nConfiguracion IA"),
        (0.8, 10.8, 2.5, "ImageUploader"),
        (3.6, 10.8, 2.5, "ScanResultsPanel"),
        (6.4, 10.8, 2.5, "ObjectDetailModal"),
        (9.2, 10.8, 2.5, "ProviderForm/Card"),
        (12.0, 10.8, 2.5, "Sidebar / Header"),
        (0.8, 9.9, 5.0, "Zustand scan.store + settings.store"),
        (6.1, 9.9, 5.5, "TanStack Query + Sonner + Axios"),
    ]
    for cx, cy, cw, ct in pres:
        draw_box(ax, cx, cy, cw, 0.55, ct, "#ecfdf5", "#064e3b", 6, "normal", EMERALD, 0.9, 0.8)

    # Application
    draw_layer(ax, 0.5, 5.8, 17, 3.2, "CAPA DE APLICACION (FastAPI + LangGraph + LangChain)", BLUE)
    app = [
        (0.8, 8.3, 5.5, "API Routers\nscan.py | objects.py | settings.py | export.py"),
        (6.6, 8.3, 4.0, "LangGraph StateGraph\ngraph.py + state.py"),
        (11.0, 8.3, 3.5, "ProviderCache\nSingleton memoria"),
        (0.8, 7.3, 5.0, "Nodos: validate_image | detection (auto-retry)"),
        (6.1, 7.3, 5.5, "Nodos: waste | energy | enrichment | persist"),
        (0.8, 6.3, 7.5, "Chains: detection_chain | waste_chain | energy_chain"),
        (8.6, 6.3, 6.0, "Prompts: detection_prompt | waste_prompt | energy_prompt"),
    ]
    for cx, cy, cw, ct in app:
        draw_box(ax, cx, cy, cw, 0.55, ct, "#eff6ff", "#1e3a5f", 6, "normal", BLUE, 0.9, 0.8)

    # Domain
    draw_layer(ax, 0.5, 3.2, 17, 2.4, "CAPA DE DOMINIO (Modelos + Schemas + Excepciones)", AMBER)
    dom = [
        (0.8, 4.8, 5.5, "Modelos ORM\nDetectedObjectORM | EnergyDataORM | AISettingsORM"),
        (6.6, 4.8, 5.5, "Schemas Pydantic\nobject_schema | settings_schema | AgentState"),
        (12.4, 4.8, 4.5, "Excepciones de Dominio\nEnergyVisionBaseError"),
        (0.8, 3.9, 7.5, "ImageValidationError | ProviderNotConfiguredError | AIInferenceError"),
    ]
    for cx, cy, cw, ct in dom:
        draw_box(ax, cx, cy, cw, 0.55, ct, "#fffbeb", "#78350f", 6, "normal", AMBER, 0.9, 0.8)

    # Infrastructure
    draw_layer(ax, 0.5, 0.5, 17, 2.5, "CAPA DE INFRAESTRUCTURA (Base de Datos + Seguridad + Proveedores IA)", PINK)
    infra = [
        (0.8, 2.3, 3.8, "SQLite + SQLAlchemy Async\naioSQLite | Alembic"),
        (4.9, 2.3, 3.8, "Repositories\nobject_repository"),
        (9.0, 2.3, 4.5, "Provider Factory\nOpenAI | Anthropic | Gemini | Ollama"),
        (13.8, 2.3, 3.2, "BaseProvider (ABC)\nget_model()"),
        (0.8, 1.3, 5.5, "Fernet (AES-128) -- cifrado API keys"),
        (6.6, 1.3, 5.5, "Pillow + python-magic"),
        (12.4, 1.3, 5.0, "FastAPI StaticFiles | CORS | Logger"),
    ]
    for cx, cy, cw, ct in infra:
        draw_box(ax, cx, cy, cw, 0.55, ct, "#fdf2f8", "#831843", 6, "normal", PINK, 0.9, 0.8)

    fig.savefig(filepath, dpi=180, bbox_inches="tight", facecolor=DARK_BG)
    plt.close(fig)
    print(f"  OK {os.path.basename(filepath)}")


def diagram_3_pipeline(filepath):
    fig, ax = plt.subplots(figsize=(14, 11))
    ax.set_xlim(0, 14); ax.set_ylim(0, 11); ax.axis("off")
    ax.set_facecolor(DARK_BG); fig.patch.set_facecolor(DARK_BG)
    ax.text(7, 10.7, "EnergyVision AI -- Grafo LangGraph (Pipeline de Deteccion)",
            ha="center", fontsize=14, fontweight="bold", color=EMERALD)

    nodes = [
        (4.5, 9.8, 5.0, 0.9, "validate_image_node\nValidar MIME, tamano, redimensionar, SHA-256", EMERALD, LIGHT_GREEN, "#064e3b"),
        (4.5, 8.2, 5.0, 1.1, "detection_node\nIdentificar objeto (modelo multimodal)\nAuto-retry si confidence < 0.4", BLUE, LIGHT_BLUE, "#1e3a5f"),
        (4.5, 6.5, 5.0, 0.9, "waste_node\nClasificar LER: codigo, peligrosidad, jerarquia", AMBER, LIGHT_AMBER, "#78350f"),
        (4.5, 4.8, 5.0, 0.9, "energy_node\nEnergy Score 0-100, kWh/unidad, kWh/kg", PINK, LIGHT_PINK, "#831843"),
        (4.5, 3.1, 5.0, 0.9, "enrichment_node\nDescripcion tecnica, sugerencias reutilizacion", PURPLE, LIGHT_PURPLE, "#4c1d95"),
        (4.5, 1.4, 5.0, 0.9, "persist_node\nGuardar imagen /uploads/, SQLite (idempotente hash)", SLATE, "#e2e8f0", "#1e293b"),
    ]
    for cx, cy, cw, ch, label, fill, edge, tc in nodes:
        draw_box(ax, cx, cy, cw, ch, label, fill, tc, 7, "normal", edge, 0.9, 1.5)

    draw_box(ax, 6.2, 10.4, 1.6, 0.5, "START", EMERALD, "white", 9, "bold")
    draw_box(ax, 6.2, 0.7, 1.6, 0.5, "END", RED, "white", 9, "bold")

    for i in range(len(nodes) - 1):
        y1 = nodes[i][1]
        y2 = nodes[i + 1][1] + nodes[i + 1][3]
        draw_arrow(ax, 7, y1, 7, y2, GRAY)

    draw_arrow(ax, 7, 10.4, 7, 9.95, GRAY)
    draw_arrow(ax, 7, nodes[-1][1], 7, 1.2, GRAY)

    # Error ends
    draw_box(ax, 10.5, 9.6, 1.8, 0.5, "END (error)", RED, "white", 7, "bold")
    draw_box(ax, 10.5, 8.0, 1.8, 0.5, "END (error)", RED, "white", 7, "bold")

    ax.annotate("", xy=(10.5, 9.6), xytext=(9.5, 9.3),
                arrowprops=dict(arrowstyle="->", color=RED, lw=1, connectionstyle="arc3,rad=0.2"))
    ax.annotate("", xy=(10.5, 8.0), xytext=(9.5, 7.8),
                arrowprops=dict(arrowstyle="->", color=RED, lw=1, connectionstyle="arc3,rad=0.2"))

    # OK labels
    ax.text(8.5, 9.5, "OK", fontsize=7, color=EMERALD, fontweight="bold")
    ax.text(8.5, 7.9, "OK", fontsize=7, color=EMERALD, fontweight="bold")
    ax.text(10.8, 9.0, "X error", fontsize=7, color=RED, fontweight="bold")
    ax.text(10.8, 7.4, "X error", fontsize=7, color=RED, fontweight="bold")

    # Annotation: Auto-Retry
    ax.text(0.5, 8.5, "Auto-Retry:\nconfidence < 0.4\n-> prompt reforzado\n-> temp 0.3",
            fontsize=7, color="#a16207", va="top",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#fefce8", edgecolor="#ca8a04", alpha=0.9))
    ax.plot([2.2, 4.5], [8.3, 8.8], color="#ca8a04", lw=1, linestyle="--")

    # Annotation: ProviderCache
    ax.text(10.5, 5.8, "ProviderCache\n(singleton)\n1 consulta DB\npara pipeline",
            fontsize=7, color=BLUE, va="top",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#eff6ff", edgecolor=BLUE, alpha=0.9))
    ax.plot([10.5, 9.5], [5.9, 6.5], color=BLUE, lw=1, linestyle="--")

    # Annotation: Idempotency
    ax.text(0.5, 1.6, "Idempotencia:\nSHA-256 imagen\nSi existe DB\n-> retorna existente",
            fontsize=7, color=SLATE, va="top",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#f1f5f9", edgecolor=SLATE, alpha=0.9))
    ax.plot([2.2, 4.5], [1.8, 1.9], color=SLATE, lw=1, linestyle="--")

    fig.savefig(filepath, dpi=180, bbox_inches="tight", facecolor=DARK_BG)
    plt.close(fig)
    print(f"  OK {os.path.basename(filepath)}")


def diagram_4_despliegue(filepath):
    fig, ax = plt.subplots(figsize=(18, 10))
    ax.set_xlim(0, 18); ax.set_ylim(0, 10); ax.axis("off")
    ax.set_facecolor(DARK_BG); fig.patch.set_facecolor(DARK_BG)
    ax.text(9, 9.6, "EnergyVision AI -- Diagrama de Despliegue Fisico",
            ha="center", fontsize=15, fontweight="bold", color=EMERALD)

    # Browser
    bx, by, bw, bh = 0.5, 0.8, 4.5, 7.5
    box = FancyBboxPatch((bx, by), bw, bh, boxstyle="round,pad=0.3",
                         facecolor=EMERALD, edgecolor=EMERALD, linewidth=2, alpha=0.10)
    ax.add_patch(box)
    ax.text(bx + bw / 2, by + bh - 0.3, "Navegador Web", ha="center", fontsize=11,
            fontweight="bold", color=EMERALD)
    ax.text(bx + bw / 2, by + bh - 0.9, "SO: Windows / macOS / Linux", ha="center",
            fontsize=7, color=GRAY)

    items_b = [
        (by + 5.0, 1.8, "SPA React 19 + Vite\n(build estatico)\nTailwind CSS 4 + Base UI"),
        (by + 2.5, 1.8, "HTTP REST (Axios)\nBase: localhost:8000\n/api/v1/*"),
        (by + 1.0, 1.0, "GET /uploads/{file}\nFastAPI StaticFiles"),
    ]
    for iy, ih, label in items_b:
        draw_box(ax, bx + 0.3, iy, bw - 0.6, ih, label, "#ecfdf5", "#064e3b", 7, "normal", EMERALD, 0.8, 1)

    # Backend Server
    sx, sy, sw, sh = 6.5, 0.8, 5.5, 7.5
    box = FancyBboxPatch((sx, sy), sw, sh, boxstyle="round,pad=0.3",
                         facecolor=BLUE, edgecolor=BLUE, linewidth=2, alpha=0.10)
    ax.add_patch(box)
    ax.text(sx + sw / 2, sy + sh - 0.3, "Servidor Backend (localhost:8000)", ha="center",
            fontsize=11, fontweight="bold", color=BLUE)
    ax.text(sx + sw / 2, sy + sh - 0.9, "Python 3.11+ | Uvicorn | FastAPI", ha="center",
            fontsize=7, color=GRAY)

    items_s = [
        (sy + 5.5, "FastAPI Application (app.main) + CORS Middleware"),
        (sy + 4.5, "POST /scan | GET /objects | PUT /settings | GET /export"),
        (sy + 3.8, "LangGraph Pipeline (6 nodos)"),
        (sy + 2.8, "Provider Factory: OpenAI | Anthropic | Gemini | Ollama"),
        (sy + 1.8, "Domain: ORM models | Pydantic schemas | Exceptions"),
        (sy + 1.0, "Infra: SQLAlchemy async | Fernet | Pillow | python-magic"),
    ]
    for iy, label in items_s:
        is_main = iy >= sy + 3.0
        draw_box(ax, sx + 0.3, iy, sw - 0.6, 0.55, label, "#eff6ff", "#1e3a5f",
                 6.5 if not is_main else 7, "normal", BLUE, 0.9 if is_main else 0.7, 1)

    # Data Layer
    dx, dy, dw, dh = 13.5, 0.8, 4.0, 7.5
    box = FancyBboxPatch((dx, dy), dw, dh, boxstyle="round,pad=0.3",
                         facecolor=PINK, edgecolor=PINK, linewidth=2, alpha=0.10)
    ax.add_patch(box)
    ax.text(dx + dw / 2, dy + dh - 0.3, "Capa de Datos\n(./data/)", ha="center",
            fontsize=10, fontweight="bold", color=PINK)

    draw_box(ax, dx + 0.3, dy + 4.5, dw - 0.6, 2.0,
             "energyvision.db (SQLite)\nTablas:\n- detected_objects\n- energy_data\n- ai_settings",
             "#fdf2f8", "#831843", 7, "normal", PINK, 0.9, 1)
    draw_box(ax, dx + 0.3, dy + 2.5, dw - 0.6, 1.5,
             "uploads/\nImagenes procesadas\n{sha256}.{jpg|png|webp}",
             "#fdf2f8", "#831843", 6.5, "normal", PINK, 0.8, 1)
    draw_box(ax, dx + 0.3, dy + 1.2, dw - 0.6, 0.9,
             "secret.key\nFernet (AES-128)",
             "#fdf2f8", "#831843", 6.5, "normal", PINK, 0.8, 1)

    # External APIs
    ex, ey, ew, eh = 1, 0.1, 16, 0.6
    box = FancyBboxPatch((ex, ey), ew, eh, boxstyle="round,pad=0.2",
                         facecolor=LIGHT_PURPLE, edgecolor=PURPLE, linewidth=1, alpha=0.15)
    ax.add_patch(box)
    ax.text(9, 0.4, "APIs Externas de IA: OpenAI | Anthropic | Google Gemini | Ollama (Local)",
            ha="center", fontsize=8, fontweight="bold", color=PURPLE)
    ax.plot([sx + 2.7, sx + 2.7], [sy + sh - 0.5, 0.8], color=PURPLE, lw=1, linestyle="--", alpha=0.5)

    # Arrows
    draw_arrow(ax, bx + bw, 4.0, sx, 4.0, GRAY, 1.5)
    ax.text(bx + bw + 0.2, 4.3, "HTTP/REST\n:8000", fontsize=7, color=GRAY)
    draw_arrow(ax, sx + sw, 4.0, dx, 4.0, GRAY, 1.5)
    ax.text(sx + sw + 0.2, 4.3, "SQLAlchemy\nasync", fontsize=7, color=GRAY)

    fig.savefig(filepath, dpi=180, bbox_inches="tight", facecolor=DARK_BG)
    plt.close(fig)
    print(f"  OK {os.path.basename(filepath)}")


print("=== Generando diagramas PNG ===")
diagram_1_alto_nivel(os.path.join(OUTPUT_DIR, "diagrama_1_alto_nivel.png"))
diagram_2_arquitectura_logica(os.path.join(OUTPUT_DIR, "diagrama_2_arquitectura_logica.png"))
diagram_3_pipeline(os.path.join(OUTPUT_DIR, "diagrama_3_pipeline_langgraph.png"))
diagram_4_despliegue(os.path.join(OUTPUT_DIR, "diagrama_4_despliegue_fisico.png"))
print("=== Diagramas generados correctamente ===")
