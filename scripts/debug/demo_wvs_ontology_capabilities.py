#!/usr/bin/env python3
"""
WVS Ontology Capabilities Demo — All 10 OntologyQuery operations
illustrated with the 5 prediction scenarios across 6 countries.

Each capability gets a concrete example showing what it returns and
how the answer changes across countries.

Usage:
    python scripts/debug/demo_wvs_ontology_capabilities.py
"""
import json
import sys
import time
from collections import defaultdict
from pathlib import Path
from textwrap import indent, fill

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "debug"))
DATA = ROOT / "data" / "results"
NAVEGADOR_DATA = Path("/workspaces/navegador_data") / "data" / "results"

COUNTRIES = ["MEX", "USA", "JPN", "DEU", "BRA", "NGA"]

# Scenario constructs (manifest key format)
CONSTRUCTS = {
    "autonomy":      "WVS_A|child_qualities_autonomy_self_expression",
    "participation": "WVS_E|online_political_participation",
    "security":      "WVS_H|precautionary_security_behaviors",
    "worry":         "WVS_H|socioeconomic_insecurity_worry",
    "trust":         "WVS_E|confidence_in_domestic_institutions",
    "morality":      "WVS_F|sexual_and_reproductive_morality_permissiveness",
    "change":        "WVS_A|societal_change_attitudes",
    "immigration":   "WVS_G|perceived_negative_effects_of_immigration",
}


def hr(title, char="═"):
    w = 78
    print(f"\n{char * w}")
    print(f"  {title}")
    print(f"{char * w}")


def sub(title):
    print(f"\n  ── {title} {'─' * max(1, 60 - len(title))}")


def build_country_oqs():
    """Build OntologyQuery per country from geographic sweep."""
    from demo_wvs_ontology import build_country_kg, build_country_fp
    from opinion_ontology import OntologyQuery

    manifest = json.load(open(DATA / "wvs_construct_manifest.json"))
    wvs_fp = json.load(open(DATA / "wvs_ses_fingerprints.json"))["fingerprints"]

    print("Loading geographic sweep...")
    geo = json.load(open(NAVEGADOR_DATA / "wvs_geographic_sweep_w7.json"))

    fp_v2 = build_country_fp(manifest, wvs_fp)
    fp_path = DATA / "_tmp_cap_fp.json"
    with open(fp_path, "w") as f:
        json.dump(fp_v2, f)

    oqs = {}
    for ctry in COUNTRIES:
        kg = build_country_kg(ctry, geo["estimates"], manifest, wvs_fp)
        kg_path = DATA / f"_tmp_cap_kg_{ctry.lower()}.json"
        with open(kg_path, "w") as f:
            json.dump(kg, f)
        oqs[ctry] = OntologyQuery(fp_path=fp_path, kg_path=kg_path, dataset=f"wvs_{ctry}")
        n_edges = sum(len(v) for v in oqs[ctry]._bridges.values()) // 2
        print(f"  {ctry}: {n_edges} edges")

    return oqs, manifest


def cleanup_temps():
    for f in DATA.glob("_tmp_cap_*"):
        f.unlink()


# ─── Capability 1: get_profile ────────────────────────────────────────

def demo_get_profile(oqs):
    hr("1. get_profile — SES fingerprint of a construct")
    print("  Returns the 4D SES fingerprint: which sociodemographic dimensions")
    print("  stratify this attitude, and in which direction.\n")

    key = CONSTRUCTS["participation"]
    print(f"  Query: get_profile('{key}')\n")

    # Show for MEX (representative — fingerprints are from MEX W7)
    oq = oqs["MEX"]
    p = oq.get_profile(key)

    print(f"  Level:         {p.get('level')}")
    print(f"  SES magnitude: {p.get('ses_magnitude', 0):.4f}")
    print(f"  Dominant dim:  {p.get('dominant_dim')}")
    fp = p.get("fingerprint", {})
    if fp:
        print(f"  Fingerprint:   escol={fp.get('rho_escol',0):+.4f}  "
              f"Tam_loc={fp.get('rho_Tam_loc',0):+.4f}  "
              f"sexo={fp.get('rho_sexo',0):+.4f}  "
              f"edad={fp.get('rho_edad',0):+.4f}")
    print(f"\n  Narrative:")
    print(indent(fill(p.get("narrative", ""), 72), "    "))


# ─── Capability 2: get_similar ────────────────────────────────────────

def demo_get_similar(oqs):
    hr("2. get_similar — Constructs with most similar SES profile")
    print("  Finds constructs whose 4D fingerprint is closest (cosine similarity).")
    print("  These are attitudes stratified by the SAME sociodemographic forces.\n")

    key = CONSTRUCTS["trust"]
    print(f"  Query: get_similar('{key}', n=5)\n")

    oq = oqs["MEX"]
    results = oq.get_similar(key, n=5)
    print(f"  {'Rank':<5} {'Cosine':>7}  Construct")
    print(f"  {'─' * 60}")
    for i, r in enumerate(results, 1):
        name = r["key"].split("|")[1].replace("_", " ")
        print(f"  {i:<5} {r['cosine_sim']:>+7.3f}  {name}")


# ─── Capability 3: explain_pair ───────────────────────────────────────

def demo_explain_pair(oqs):
    hr("3. explain_pair — Why two constructs co-vary (or don't)")
    print("  For a pair of constructs, explains the SES geometry:")
    print("  cosine similarity, shared dimension, and expected co-variation direction.\n")

    pairs = [
        (CONSTRUCTS["participation"], CONSTRUCTS["security"], "S2: Participation ↔ Security"),
        (CONSTRUCTS["morality"], CONSTRUCTS["change"], "S4: Morality ↔ Change"),
    ]

    for key_a, key_b, label in pairs:
        sub(label)
        oq = oqs["MEX"]
        exp = oq.explain_pair(key_a, key_b)

        print(f"    Cosine similarity:  {exp.get('cosine_sim', 0):+.3f}")
        print(f"    Expected direction: {exp.get('covariation', '?')}")
        print(f"    Shared SES dim:    {exp.get('shared_dim', '?')}")
        print(f"    Narrative:")
        print(indent(fill(exp.get("narrative", ""), 68), "      "))


# ─── Capability 4: get_neighbors — per country ───────────────────────

def demo_get_neighbors(oqs):
    hr("4. get_neighbors — Bridge-connected constructs (cross-country)")
    print("  Returns all constructs with a significant SES-mediated bridge (γ).")
    print("  The SAME construct can have DIFFERENT neighbors in different countries.\n")

    key = CONSTRUCTS["participation"]
    name = "online political participation"

    for ctry in ["MEX", "USA", "JPN", "DEU"]:
        sub(f"{ctry} — neighbors of '{name}'")
        oq = oqs[ctry]
        nb = oq.get_neighbors(key, top_n=5)
        if not nb:
            print("    (no significant neighbors)")
            continue
        print(f"    {'γ':>8}  {'Construct':<45}  {'Shared dim'}")
        print(f"    {'─' * 65}")
        for n in nb[:5]:
            cname = n["neighbor"].split("|")[1].replace("_", " ")[:42]
            dim = n.get("shared_dim", "?")
            print(f"    {n['gamma']:>+8.4f}  {cname:<45}  {dim}")


# ─── Capability 5: get_neighborhood — summary ────────────────────────

def demo_get_neighborhood(oqs):
    hr("5. get_neighborhood — Attitudinal neighborhood summary")
    print("  Lifts any key (item, construct, domain) to an L1 anchor,")
    print("  then returns summary: domain distribution, pos/neg balance, strongest edge.\n")

    key = CONSTRUCTS["trust"]

    for ctry in ["MEX", "DEU", "NGA"]:
        sub(f"{ctry}")
        oq = oqs[ctry]
        nh = oq.get_neighborhood(key, top_n=10)
        s = nh["neighborhood_summary"]
        print(f"    Anchor:     {nh['anchor_construct']}")
        print(f"    Neighbors:  {s['n_neighbors']} (pos γ: {s['positive_gamma']}, neg γ: {s['negative_gamma']})")
        print(f"    Domains:    {s['domain_distribution']}")
        print(f"    Shared dim: {s['dominant_shared_dim']}")
        st = s.get("strongest_edge")
        if st:
            sn = st["neighbor"].split("|")[1].replace("_", " ")[:35]
            print(f"    Strongest:  {sn} (γ={st['gamma']:+.4f})")


# ─── Capability 6: find_path — Dijkstra shortest bridge path ─────────

def demo_find_path(oqs):
    hr("6. find_path — Strongest bridge path between two constructs")
    print("  Dijkstra with weight=-log(|γ|): maximizes product of |γ| along the path.")
    print("  Shows HOW two distant attitudes connect through intermediate constructs.\n")

    pairs = [
        (CONSTRUCTS["autonomy"], CONSTRUCTS["immigration"],
         "Autonomy values → Anti-immigration attitudes"),
        (CONSTRUCTS["worry"], CONSTRUCTS["morality"],
         "Economic worry → Moral permissiveness"),
    ]

    for key_a, key_b, label in pairs:
        sub(label)
        for ctry in ["MEX", "USA", "JPN", "DEU"]:
            oq = oqs[ctry]
            path = oq.find_path(key_a, key_b)
            if path.get("error"):
                print(f"    {ctry}: {path['error']}")
                continue

            hops = len(path["path"]) - 1
            sig = path["signal_chain"]
            sign_note = path.get("expected_sign_note", "?")

            # Format path
            steps = []
            for i, node in enumerate(path["path"]):
                name = node.split("|")[1].replace("_", " ")[:25]
                steps.append(name)

            edges_str = ""
            for e in path.get("edges", []):
                edges_str += f" →[γ={e['gamma']:+.4f}]→ "

            print(f"    {ctry}: {' → '.join(steps)}")
            print(f"          {hops} hops, signal={sig:.6f}, expected: {sign_note}")


# ─── Capability 7: get_camp — Bipartition membership ─────────────────

def demo_get_camp(oqs):
    hr("7. get_camp — Cosmopolitan vs Tradition camp assignment")
    print("  Signed Laplacian Fiedler bipartition: +1=cosmopolitan, -1=tradition.")
    print("  Shows whether a construct is associated with modern/urban or traditional/rural SES.\n")

    keys = [
        ("autonomy", CONSTRUCTS["autonomy"]),
        ("participation", CONSTRUCTS["participation"]),
        ("security", CONSTRUCTS["security"]),
        ("morality", CONSTRUCTS["morality"]),
        ("trust", CONSTRUCTS["trust"]),
    ]

    print(f"  {'Construct':<25}", end="")
    for ctry in COUNTRIES:
        print(f" {ctry:>8}", end="")
    print()
    print(f"  {'─' * 75}")

    for label, key in keys:
        print(f"  {label:<25}", end="")
        for ctry in COUNTRIES:
            oq = oqs[ctry]
            camp = oq.get_camp(key)
            name = camp.get("camp_name", "?")
            conf = camp.get("confidence", 0)
            short = "C" if name == "cosmopolitan" else "T" if name == "tradition" else "?"
            print(f" {short}({conf:.2f})", end="")
        print()

    print("\n  C = cosmopolitan, T = tradition, (confidence 0-1)")
    print("  Note: the SAME construct can flip camps across countries!")


# ─── Capability 8: get_network — BFS subgraph ────────────────────────

def demo_get_network(oqs):
    hr("8. get_network — BFS subgraph expansion")
    print("  Expands from a seed construct to N hops, returning nodes + edges.")
    print("  Shows the local structure around an attitude.\n")

    key = CONSTRUCTS["trust"]

    for ctry in ["MEX", "DEU", "NGA"]:
        sub(f"{ctry} — 1-hop network from 'institutional trust'")
        oq = oqs[ctry]
        net = oq.get_network(key, hops=1)
        n_nodes = len(net["nodes"])
        n_edges = len(net["edges"])
        domains = set(k.split("|")[0] for k in net["nodes"])
        print(f"    {n_nodes} nodes, {n_edges} edges, spanning domains: {sorted(domains)}")

        sub(f"{ctry} — 2-hop network")
        net2 = oq.get_network(key, hops=2)
        print(f"    {len(net2['nodes'])} nodes, {len(net2['edges'])} edges")
        print(f"    (1→2 hop expansion: {len(net2['nodes'])-n_nodes} new nodes)")


# ─── Capability 9: get_domain_landscape ───────────────────────────────

def demo_get_domain_landscape(oqs):
    hr("9. get_domain_landscape — All constructs in a domain, by SES magnitude")
    print("  Shows which constructs in a domain are most SES-stratified.\n")

    domain = "WVS_E"
    oq = oqs["MEX"]
    landscape = oq.get_domain_landscape(domain)

    if not landscape:
        print("  No data for this domain")
        return

    constructs = landscape.get("constructs", [])
    print(f"  Domain: {domain} (Politics & Society) — {len(constructs)} constructs")
    print(f"  {'Construct':<45} {'Magnitude':>10} {'Dominant':>10}")
    print(f"  {'─' * 68}")
    for item in constructs:
        name = item["key"].split("|")[1].replace("_", " ")[:42]
        mag = item.get("ses_magnitude", 0)
        dom_dim = item.get("dominant_dim", "?")
        print(f"  {name:<45} {mag:>10.4f} {dom_dim:>10}")


# ─── Capability 10: get_frustrated_nodes ──────────────────────────────

def demo_get_frustrated_nodes(oqs):
    hr("10. get_frustrated_nodes — Constructs straddling the camp boundary")
    print("  Nodes with high frustrated triangle ratio sit between the two camps.")
    print("  Predictions through these nodes carry higher uncertainty.\n")

    for ctry in ["MEX", "USA", "DEU"]:
        sub(ctry)
        oq = oqs[ctry]
        frust = oq.get_frustrated_nodes(min_frustrated_ratio=0.05)
        if not frust:
            print("    No frustrated nodes above threshold")
            continue
        print(f"    {len(frust)} frustrated node(s):")
        for f in frust[:5]:
            name = f["construct"].split("|")[1].replace("_", " ")[:35]
            camp = f.get("camp_name", "?")
            ratio = f.get("frustrated_ratio", 0)
            print(f"      {name:<38} camp={camp}  frustrated={ratio:.1%}")


# ─── Main ─────────────────────────────────────────────────────────────

def main():
    t0 = time.time()
    print("WVS Ontology Capabilities Demo")
    print("All 10 OntologyQuery operations, illustrated across countries")
    print("=" * 78)

    oqs, manifest = build_country_oqs()

    demo_get_profile(oqs)
    demo_get_similar(oqs)
    demo_explain_pair(oqs)
    demo_get_neighbors(oqs)
    demo_get_neighborhood(oqs)
    demo_find_path(oqs)
    demo_get_camp(oqs)
    demo_get_network(oqs)
    demo_get_domain_landscape(oqs)
    demo_get_frustrated_nodes(oqs)

    cleanup_temps()

    hr("SUMMARY", "═")
    print("  10 ontology operations demonstrated across 6 countries.")
    print("  Key cross-country findings:")
    print("  • get_neighbors: Same construct has different bridge partners per country")
    print("  • get_camp: Constructs can flip cosmopolitan↔tradition across cultures")
    print("  • find_path: Bridge chains use different intermediaries per country")
    print("  • get_frustrated_nodes: Boundary constructs vary by national context")
    print(f"\n  Done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
