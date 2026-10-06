"""Habitat potential H per stand and mushroom species (docs/SPEC.md, chapter 3).

Pure functions: all numbers come from the `params` dict (pipeline/config/model_params.yaml).
"""

from collections.abc import Sequence


def tree_group(species_code: str | None, params: dict) -> str:
    """BDL species code (e.g. 'DB.B') -> tree group (e.g. 'Db'); unknown -> 'inne'."""
    if not species_code:
        return "inne"
    prefix = species_code.split(".")[0].strip().upper()
    return params["tree_code_map"].get(prefix, "inne")


def tree_value(species: str, group: str, params: dict) -> float:
    table = params["tree"][species]
    return table.get(group, table["inne"])


def suit_tree(species: str, dominant_code: str | None, share_tenths: int | None, params: dict) -> float:
    """Dominant species weighted by its share; the remainder counts as 'inne' (SPEC 3.1)."""
    share = min(max((share_tenths if share_tenths is not None else 10) / 10, 0.0), 1.0)
    dominant = tree_value(species, tree_group(dominant_code, params), params)
    return share * dominant + (1 - share) * params["tree"][species]["inne"]


def suit_tree_mix(species: str, mix: Sequence[Sequence], params: dict) -> float:
    """Tree suitability for an explicit mix [[group, share], ...] (forests outside LP)."""
    return sum(share * tree_value(species, group, params) for group, share in mix)


def interp_nodes(x: float, nodes: Sequence[Sequence[float]]) -> float:
    """Piecewise-linear interpolation through (x, y) nodes, constant outside the range."""
    if x <= nodes[0][0]:
        return float(nodes[0][1])
    for (x0, y0), (x1, y1) in zip(nodes, nodes[1:]):
        if x <= x1:
            return float(y0 + (y1 - y0) * (x - x0) / (x1 - x0))
    return float(nodes[-1][1])


def suit_age(species: str, age: float | None, params: dict) -> float:
    if age is None:
        return params["non_lp"]["age_factor"]
    return interp_nodes(age, params["age_nodes"][species])


def suit_habitat(species: str, site_type: str | None, params: dict) -> float:
    if not site_type:
        return params["hab_default"]
    return params["habitat"][species].get(site_type.strip().upper(), params["hab_default"])


def is_crop(age: float | None, params: dict) -> bool:
    """Forest crop (young stand < ~4 m): permanent entry ban and H = 0."""
    return age is not None and age <= params["crop_age_max"]


def h_stand(species: str, dominant_code: str | None, share_tenths: int | None, age: float | None,
            site_type: str | None, params: dict) -> float:
    """H for one BDL stand (SPEC 3.1)."""
    if is_crop(age, params):
        return 0.0
    return (suit_tree(species, dominant_code, share_tenths, params)
            * suit_age(species, age, params)
            * suit_habitat(species, site_type, params))


def h_non_lp(species: str, leaf_type: str | None, params: dict) -> float:
    """H for a forest outside the State Forests (OSM polygon, no stand data; SPEC 3.5)."""
    mixes = params["non_lp"]["leaf_type_trees"]
    mix = mixes.get(leaf_type or "unknown", mixes["unknown"])
    return suit_tree_mix(species, mix, params) * params["non_lp"]["age_factor"] * params["hab_default"]


def h_all(stand_kwargs: dict, params: dict) -> dict[str, float]:
    """H for every species plus h_max."""
    values = {sp: h_stand(sp, params=params, **stand_kwargs) for sp in params["species"]}
    values["h_max"] = max(values.values())
    return values
