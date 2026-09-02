"""
Wizualizacja 3D ułożenia produktów w kartonie (matplotlib + mplot3d).

Moduł jest celowo oddzielony od logiki pakowania - przyjmuje gotowy
PackingResult i tylko go rysuje.
"""

from __future__ import annotations

from collections.abc import Sequence

import matplotlib
matplotlib.use("Agg")          # tryb bez okna - zapis prosto do pliku PNG

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from mpl_toolkits.mplot3d.art3d import Line3DCollection, Poly3DCollection

from packing import Container, PackingResult, Placement

# Domyślna paleta kolorów dla kolejnych typów produktów.
_PALETTE = [
    "#4C9BE8", "#F2994A", "#4CB782", "#E4586B",
    "#9B7EDE", "#F2C94C", "#00B8B8", "#B85C9E",
]


def _cuboid_faces(x, y, z, dx, dy, dz) -> list[list[tuple[float, float, float]]]:
    """Zwraca 6 ścian prostopadłościanu jako listy wierzchołków."""
    x2, y2, z2 = x + dx, y + dy, z + dz
    return [
        [(x, y, z), (x2, y, z), (x2, y2, z), (x, y2, z)],       # dół
        [(x, y, z2), (x2, y, z2), (x2, y2, z2), (x, y2, z2)],   # góra
        [(x, y, z), (x2, y, z), (x2, y, z2), (x, y, z2)],       # przód
        [(x, y2, z), (x2, y2, z), (x2, y2, z2), (x, y2, z2)],   # tył
        [(x, y, z), (x, y2, z), (x, y2, z2), (x, y, z2)],       # lewo
        [(x2, y, z), (x2, y2, z), (x2, y2, z2), (x2, y, z2)],   # prawo
    ]


def _cuboid_edges(x, y, z, dx, dy, dz) -> list[tuple[tuple, tuple]]:
    """12 krawędzi prostopadłościanu - używane do obrysu kartonu."""
    x2, y2, z2 = x + dx, y + dy, z + dz
    c = [(x, y, z), (x2, y, z), (x2, y2, z), (x, y2, z),
         (x, y, z2), (x2, y, z2), (x2, y2, z2), (x, y2, z2)]
    idx = [(0, 1), (1, 2), (2, 3), (3, 0),
           (4, 5), (5, 6), (6, 7), (7, 4),
           (0, 4), (1, 5), (2, 6), (3, 7)]
    return [(c[i], c[j]) for i, j in idx]


def color_map(result: PackingResult) -> dict[str, str]:
    """Przypisuje kolor każdemu typowi produktu (własny kolor ma pierwszeństwo)."""
    colors: dict[str, str] = {}
    for i, product in enumerate(result.products):
        colors[product.name] = product.color or _PALETTE[i % len(_PALETTE)]
    return colors


def _draw_container(ax, container: Container) -> None:
    """Rysuje karton jako przezroczystą bryłę z wyraźnym obrysem krawędzi."""
    edges = _cuboid_edges(0, 0, 0, container.length, container.width, container.height)
    ax.add_collection3d(Line3DCollection(edges, colors="#37474F",
                                         linewidths=1.6, zorder=1))
    # delikatnie zaznaczone dno, żeby było widać podstawę kartonu
    floor = [[(0, 0, 0), (container.length, 0, 0),
              (container.length, container.width, 0), (0, container.width, 0)]]
    ax.add_collection3d(Poly3DCollection(floor, facecolors="#37474F",
                                         alpha=0.06, edgecolors="none"))


def _draw_items(ax, placements: Sequence[Placement], colors: dict[str, str],
                alpha: float = 0.92) -> None:
    """Rysuje produkty jako kolorowe prostopadłościany.

    Rysujemy od najdalszych do najbliższych obserwatora, bo matplotlib
    nie ma prawdziwego bufora głębi dla Poly3DCollection.
    """
    ordered = sorted(placements, key=lambda p: (p.z, p.y, p.x))
    for p in ordered:
        faces = _cuboid_faces(p.x, p.y, p.z, p.dx, p.dy, p.dz)
        ax.add_collection3d(Poly3DCollection(
            faces,
            facecolors=colors.get(p.product, "#999999"),
            edgecolors="#1B2631",
            linewidths=0.45,
            alpha=alpha,
        ))


def _style_axes(ax, container: Container, title: str | None = None,
                hide: Sequence[str] = (), label_size: int = 10) -> None:
    """Ustawia zakresy, proporcje i opisy osi zgodnie z wymiarami kartonu.

    `hide` pozwala wygasić osie, które w danym ujęciu i tak są nieczytelne
    (np. oś Y w widoku z przodu - patrzymy dokładnie wzdłuż niej).
    """
    ax.set_xlim(0, container.length)
    ax.set_ylim(0, container.width)
    ax.set_zlim(0, container.height)
    # proporcje 1:1:1 w cm - inaczej karton 40x40x60 wyglądałby jak sześcian
    ax.set_box_aspect((container.length, container.width, container.height))
    ax.set_xlabel("długość X [cm]", labelpad=8, fontsize=label_size)
    ax.set_ylabel("szerokość Y [cm]", labelpad=8, fontsize=label_size)
    ax.set_zlabel("wysokość Z [cm]", labelpad=8, fontsize=label_size)
    ax.tick_params(labelsize=max(6, label_size - 2))
    ax.grid(False)
    for pane in (ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane):
        pane.fill = False
        pane.set_edgecolor("#CFD8DC")
    for name in hide:
        # Nie usuwamy podziałek (mplot3d tego nie lubi) - tylko je wygaszamy.
        axis = {"x": ax.xaxis, "y": ax.yaxis, "z": ax.zaxis}[name]
        axis.set_tick_params(labelcolor="none", colors="none")
        axis.set_label_text("")
        axis.line.set_color("none")
    if title:
        ax.set_title(title, fontsize=11, pad=6)


def _legend_handles(result: PackingResult, colors: dict[str, str]) -> list:
    """Legenda: kolor + nazwa + ile sztuk zapakowano z ilu dostępnych."""
    packed = result.packed_counts
    handles = []
    for product in result.products:
        handles.append(Patch(
            facecolor=colors[product.name], edgecolor="#1B2631",
            label=(f"{product.name}  "
                   f"({product.length:g}×{product.width:g}×{product.height:g} cm, "
                   f"{'obrót OK' if product.rotatable else 'bez obrotu'})  "
                   f"— {packed.get(product.name, 0)}/{product.quantity} szt."),
        ))
    handles.append(Line2D([0], [0], color="#37474F", lw=1.6,
                          label=(f"{result.container.name} "
                                 f"{result.container.length:g}×"
                                 f"{result.container.width:g}×"
                                 f"{result.container.height:g} cm")))
    return handles


def render_main_view(result: PackingResult, path: str,
                     elev: float = 22, azim: float = -58) -> str:
    """Główna wizualizacja 3D - jedno duże ujęcie z legendą i podsumowaniem."""
    colors = color_map(result)
    fig = plt.figure(figsize=(11, 9))
    ax = fig.add_subplot(111, projection="3d")

    _draw_container(ax, result.container)
    _draw_items(ax, result.placements, colors)
    _style_axes(ax, result.container)
    ax.view_init(elev=elev, azim=azim)

    total_qty = sum(p.quantity for p in result.products)
    fig.suptitle("Rozmieszczenie produktów w kartonie (3D bin packing)",
                 fontsize=15, fontweight="bold", y=0.975)
    fig.text(
        0.5, 0.935,
        f"zapakowano {len(result.placements)}/{total_qty} szt.   •   "
        f"wykorzystanie objętości {result.fill_ratio * 100:.2f}%   •   "
        f"wysokość stosu {result.max_used_height:g} cm",
        ha="center", va="top", fontsize=10, color="#455A64",
    )
    fig.legend(handles=_legend_handles(result, colors), loc="lower center",
               ncol=1, frameon=False, fontsize=9, bbox_to_anchor=(0.5, 0.005))

    fig.subplots_adjust(left=0.02, right=0.98, top=0.90, bottom=0.13)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def render_multi_view(result: PackingResult, path: str) -> str:
    """Cztery ujęcia z różnych stron - ułatwiają ocenę ułożenia w środku."""
    colors = color_map(result)
    # (elewacja, azymut, tytuł, osie do ukrycia w danym ujęciu)
    views = [(22, -58, "widok 3/4 (przód-lewo)", ()),
             (22, 32, "widok 3/4 (tył-prawo)", ()),
             (6, -90, "widok z przodu (płaszczyzna XZ)", ("y",)),
             (89, -90, "widok z góry (płaszczyzna XY)", ("z",))]

    fig = plt.figure(figsize=(13, 12))
    for i, (elev, azim, title, hide) in enumerate(views, start=1):
        ax = fig.add_subplot(2, 2, i, projection="3d")
        _draw_container(ax, result.container)
        _draw_items(ax, result.placements, colors)
        _style_axes(ax, result.container, title, hide=hide, label_size=9)
        ax.view_init(elev=elev, azim=azim)

    fig.suptitle("Ułożenie produktów - cztery ujęcia", fontsize=15,
                 fontweight="bold", y=0.97)
    fig.legend(handles=_legend_handles(result, colors), loc="lower center",
               ncol=1, frameon=False, fontsize=9, bbox_to_anchor=(0.5, 0.01))
    fig.subplots_adjust(left=0.02, right=0.98, top=0.94, bottom=0.10,
                        wspace=0.02, hspace=0.22)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def render_layers(result: PackingResult, path: str) -> str | None:
    """Rzuty z góry dla kolejnych poziomów - pokazują to, co schowane w środku.

    Produkty grupujemy po współrzędnej Z ich podstawy: jedna podpłaszczyzna
    wykresu = jeden poziom, na którym coś postawiono.
    """
    if not result.placements:
        return None

    colors = color_map(result)
    levels = sorted({round(p.z, 6) for p in result.placements})
    cols = min(4, len(levels))
    rows = (len(levels) + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(3.4 * cols, 3.6 * rows),
                             squeeze=False)
    for i, level in enumerate(levels):
        ax = axes[i // cols][i % cols]
        items = [p for p in result.placements if round(p.z, 6) == level]
        for p in items:
            ax.add_patch(plt.Rectangle((p.x, p.y), p.dx, p.dy,
                                       facecolor=colors.get(p.product, "#999"),
                                       edgecolor="#1B2631", linewidth=0.6))
        ax.set_xlim(0, result.container.length)
        ax.set_ylim(0, result.container.width)
        ax.set_aspect("equal")
        ax.set_title(f"poziom z = {level:g} cm  ({len(items)} szt.)", fontsize=9)
        ax.tick_params(labelsize=7)

    # ukryj nieużyte podwykresy
    for j in range(len(levels), rows * cols):
        axes[j // cols][j % cols].axis("off")

    fig.suptitle("Rzuty z góry - kolejne poziomy ułożenia", fontsize=14,
                 fontweight="bold")
    fig.legend(handles=_legend_handles(result, colors), loc="lower center",
               ncol=1, frameon=False, fontsize=9)
    fig.subplots_adjust(top=0.90, bottom=0.10 + 0.02 * len(result.products),
                        wspace=0.25, hspace=0.30)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path
