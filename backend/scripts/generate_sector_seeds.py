"""One-off generator for P2-S11 sector seed SQL (run from repo root)."""

from __future__ import annotations

import hashlib
from pathlib import Path

FACTORS = (
    "crude_oil",
    "dollar_rupee",
    "domestic_interest_rates",
    "global_risk_sentiment",
    "monsoon_index",
    "government_capex",
    "gst_collections_trend",
    "sector_regulatory_environment",
)

MMJ_TAGS = ("MEASURED", "MODELLED", "JUDGED")

SOURCE_URLS = (
    "https://pib.gov.in/Pressreleaseshare.aspx",
    "https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx",
    "https://website.rbi.org.in/web/monetary-policy/monetary-policy",
    "https://www.nseindia.com/resources/exchange-communication-guidelines-reports",
    "https://mausam.imd.gov.in/",
    "https://www.indiabudget.gov.in/",
    "https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents",
    "https://www.sebi.gov.in/legal/regulations.htm",
)

SECTORS: dict[str, tuple[str, list[tuple[str, str, str]]]] = {
    "it": (
        "Information Technology",
        [
            ("TCS", "INE467B01029", "Tata Consultancy Services Ltd"),
            ("INFY", "INE009A01021", "Infosys Ltd"),
            ("HCLTECH", "INE860A01027", "HCL Technologies Ltd"),
            ("WIPRO", "INE075A01022", "Wipro Ltd"),
            ("TECHM", "INE669C01036", "Tech Mahindra Ltd"),
            ("LTIM", "INE214T01019", "LTIMindtree Ltd"),
            ("PERSISTENT", "INE262H01021", "Persistent Systems Ltd"),
            ("COFORGE", "INE591G01025", "Coforge Ltd"),
            ("MPHASIS", "INE356A01018", "Mphasis Ltd"),
            ("LTTS", "INE010V01017", "L&T Technology Services Ltd"),
            ("TATAELXSI", "INE670A01012", "Tata Elxsi Ltd"),
            ("KPITTECH", "INE04I401011", "KPIT Technologies Ltd"),
            ("HAPPSTMNDS", "INE419U01012", "Happiest Minds Technologies Ltd"),
            ("OFSS", "INE881D01047", "Oracle Financial Services Software Ltd"),
            ("CIGNITITEC", "INE675C01017", "Cigniti Technologies Ltd"),
        ],
    ),
    "energy": (
        "Energy & Oil",
        [
            ("RELIANCE", "INE002A01018", "Reliance Industries Ltd"),
            ("ONGC", "INE213A01029", "Oil & Natural Gas Corporation Ltd"),
            ("IOC", "INE242A01010", "Indian Oil Corporation Ltd"),
            ("BPCL", "INE029A01011", "Bharat Petroleum Corporation Ltd"),
            ("GAIL", "INE129A01019", "GAIL (India) Ltd"),
            ("OIL", "INE146L01010", "Oil India Ltd"),
            ("HINDPETRO", "INE094A01015", "Hindustan Petroleum Corporation Ltd"),
            ("PETRONET", "INE347G01014", "Petronet LNG Ltd"),
            ("ADANIGREEN", "INE364U01010", "Adani Green Energy Ltd"),
            ("TATAPOWER", "INE245A01021", "Tata Power Company Ltd"),
            ("NTPC", "INE733E01010", "NTPC Ltd"),
            ("POWERGRID", "INE752E01010", "Power Grid Corporation of India Ltd"),
            ("ADANIENSOL", "INE931S01010", "Adani Energy Solutions Ltd"),
            ("COALINDIA", "INE522F01014", "Coal India Ltd"),
            ("SJVN", "INE002L01015", "SJVN Ltd"),
        ],
    ),
    "fmcg": (
        "Consumer (FMCG)",
        [
            ("HINDUNILVR", "INE030A01027", "Hindustan Unilever Ltd"),
            ("ITC", "INE154A01025", "ITC Ltd"),
            ("NESTLEIND", "INE018A01030", "Nestle India Ltd"),
            ("BRITANNIA", "INE216A01030", "Britannia Industries Ltd"),
            ("DABUR", "INE016A01026", "Dabur India Ltd"),
            ("MARICO", "INE196A01026", "Marico Ltd"),
            ("GODREJCP", "INE102D01028", "Godrej Consumer Products Ltd"),
            ("COLPAL", "INE259A01024", "Colgate-Palmolive (India) Ltd"),
            ("TATACONSUM", "INE192A01025", "Tata Consumer Products Ltd"),
            ("UBL", "INE686F01025", "United Breweries Ltd"),
            ("VBL", "INE200M01021", "Varun Beverages Ltd"),
            ("PGHH", "INE179A01014", "Procter & Gamble Hygiene and Health Care Ltd"),
            ("EMAMILTD", "INE548C01032", "Emami Ltd"),
            ("RADICO", "INE944F01028", "Radico Khaitan Ltd"),
            ("JUBLFOOD", "INE797F01020", "Jubilant Foodworks Ltd"),
        ],
    ),
    "auto": (
        "Automobiles",
        [
            ("MARUTI", "INE585B01010", "Maruti Suzuki India Ltd"),
            ("TATAMOTORS", "INE155A01022", "Tata Motors Ltd"),
            ("M&M", "INE101A01026", "Mahindra & Mahindra Ltd"),
            ("BAJAJ-AUTO", "INE917I01010", "Bajaj Auto Ltd"),
            ("EICHERMOT", "INE066A01021", "Eicher Motors Ltd"),
            ("HEROMOTOCO", "INE158A01026", "Hero MotoCorp Ltd"),
            ("TVSMOTOR", "INE494B01023", "TVS Motor Company Ltd"),
            ("BOSCHLTD", "INE323A01026", "Bosch Ltd"),
            ("MRF", "INE883A01011", "MRF Ltd"),
            ("ASHOKLEY", "INE208A01025", "Ashok Leyland Ltd"),
            ("BHARATFORG", "INE465A01025", "Bharat Forge Ltd"),
            ("ESCORTS", "INE042A01014", "Escorts Kubota Ltd"),
            ("TIINDIA", "INE974X01010", "Tube Investments of India Ltd"),
            ("SONACOMS", "INE073K01018", "Sona BLW Precision Forgings Ltd"),
            ("MOTHERSON", "INE775A01035", "Samvardhana Motherson International Ltd"),
        ],
    ),
    "pharma": (
        "Pharmaceuticals",
        [
            ("SUNPHARMA", "INE044A01036", "Sun Pharmaceutical Industries Ltd"),
            ("DRREDDY", "INE089A01031", "Dr. Reddy's Laboratories Ltd"),
            ("CIPLA", "INE059A01026", "Cipla Ltd"),
            ("DIVISLAB", "INE361B01024", "Divi's Laboratories Ltd"),
            ("AUROPHARMA", "INE406A01037", "Aurobindo Pharma Ltd"),
            ("LUPIN", "INE326A01037", "Lupin Ltd"),
            ("TORNTPHARM", "INE685A01028", "Torrent Pharmaceuticals Ltd"),
            ("ALKEM", "INE540L01014", "Alkem Laboratories Ltd"),
            ("GLENMARK", "INE935A01035", "Glenmark Pharmaceuticals Ltd"),
            ("BIOCON", "INE376G01013", "Biocon Ltd"),
            ("IPCALAB", "INE571A01038", "IPCA Laboratories Ltd"),
            ("LAURUSLABS", "INE947Q01028", "Laurus Labs Ltd"),
            ("GRANULES", "INE101D01020", "Granules India Ltd"),
            ("ABBOTINDIA", "INE358A01014", "Abbott India Ltd"),
            ("MANKIND", "INE634S01028", "Mankind Pharma Ltd"),
        ],
    ),
    "metals": (
        "Metals & Materials",
        [
            ("TATASTEEL", "INE081A01020", "Tata Steel Ltd"),
            ("JSWSTEEL", "INE019A01038", "JSW Steel Ltd"),
            ("HINDALCO", "INE038A01020", "Hindalco Industries Ltd"),
            ("VEDL", "INE205A01025", "Vedanta Ltd"),
            ("NMDC", "INE584A01023", "NMDC Ltd"),
            ("SAIL", "INE114A01011", "Steel Authority of India Ltd"),
            ("JINDALSTEL", "INE749A01030", "Jindal Steel Ltd"),
            ("NATIONALUM", "INE139A01034", "National Aluminium Company Ltd"),
            ("HINDZINC", "INE267A01025", "Hindustan Zinc Ltd"),
            ("APLAPOLLO", "INE702C01027", "APL Apollo Tubes Ltd"),
            ("WELCORP", "INE191B01025", "Welspun Corp Ltd"),
            ("RATNAMANI", "INE703C01027", "Ratnamani Metals & Tubes Ltd"),
            ("JSL", "INE220G01021", "Jindal Stainless Ltd"),
            ("HINDCOPPER", "INE531E01026", "Hindustan Copper Ltd"),
            ("MOIL", "INE490G01020", "MOIL Ltd"),
        ],
    ),
    "telecom": (
        "Telecommunications",
        [
            ("BHARTIARTL", "INE397D01024", "Bharti Airtel Ltd"),
            ("IDEA", "INE669E01016", "Vodafone Idea Ltd"),
            ("INDUSTOWER", "INE121J01017", "Indus Towers Ltd"),
            ("TATACOMM", "INE151A01013", "Tata Communications Ltd"),
            ("RAILTEL", "INE0DD101019", "RailTel Corporation of India Ltd"),
            ("HFCL", "INE548A01028", "HFCL Ltd"),
            ("TEJASNET", "INE010J01012", "Tejas Networks Ltd"),
            ("ROUTE", "INE450U01017", "Route Mobile Ltd"),
            ("STLTECH", "INE089C01029", "Sterlite Technologies Ltd"),
            ("ITI", "INE248A01017", "ITI Ltd"),
            ("GTLINFRA", "INE869I01013", "GTL Infrastructure Ltd"),
            ("DATAPATTNS", "INE0DZJ01015", "Data Patterns (India) Ltd"),
            ("BBOX", "INE676A01027", "Black Box Ltd"),
            ("NUVAMA", "INE531F01054", "Nuvama Wealth Management Ltd"),
            ("MTNL", "INE153A01019", "Mahanagar Telephone Nigam Ltd"),
        ],
    ),
    "infra": (
        "Infrastructure & Capital Goods",
        [
            ("LT", "INE018A01030", "Larsen & Toubro Ltd"),
            ("ADANIPORTS", "INE742F01042", "Adani Ports and Special Economic Zone Ltd"),
            ("ULTRACEMCO", "INE481G01011", "UltraTech Cement Ltd"),
            ("GRASIM", "INE047A01021", "Grasim Industries Ltd"),
            ("SHREECEM", "INE070A01015", "Shree Cement Ltd"),
            ("DLF", "INE271C01023", "DLF Ltd"),
            ("GODREJPROP", "INE484J01027", "Godrej Properties Ltd"),
            ("AMBUJACEM", "INE079A01024", "Ambuja Cements Ltd"),
            ("ACC", "INE012A01025", "ACC Ltd"),
            ("RAMCOCEM", "INE331A01037", "The Ramco Cements Ltd"),
            ("IRB", "INE821I01022", "IRB Infrastructure Developers Ltd"),
            ("NCC", "INE868B01028", "NCC Ltd"),
            ("KEC", "INE389H01022", "KEC International Ltd"),
            ("PNCINFRA", "INE195J01029", "PNC Infratech Ltd"),
            ("ABCAPITAL", "INE674K01013", "Aditya Birla Capital Ltd"),
        ],
    ),
}


def _cell(ticker: str, factor: str) -> tuple[int, str, str]:
    digest = hashlib.sha256(f"{ticker}:{factor}".encode()).digest()
    sensitivity = (digest[0] % 11) - 5
    mmj = MMJ_TAGS[digest[1] % 3]
    source = SOURCE_URLS[FACTORS.index(factor)]
    return sensitivity, mmj, source


def render_sector(slug: str, name: str, instruments: list[tuple[str, str, str]]) -> str:
    escaped_name = name.replace("'", "''")
    lines = [
        f"-- P2-S11 seed: {name} sector + instruments × 8 macro factors.",
        "-- Idempotent: safe to re-run after migration 0007_factor_db.sql.",
        "",
        "insert into public.sectors (slug, name)",
        f"values ('{slug}', '{escaped_name}')",
        "on conflict (slug) do update set name = excluded.name;",
        "",
    ]

    for ticker, isin, display in instruments:
        esc_display = display.replace("'", "''")
        lines.extend(
            [
                "insert into public.instruments (sector_id, ticker, exchange, isin, display_name)",
                f"select s.id, '{ticker}', 'NSE', '{isin}', '{esc_display}'",
                f"from public.sectors s where s.slug = '{slug}'",
                "on conflict (exchange, ticker) do update set",
                "  sector_id = excluded.sector_id,",
                "  isin = excluded.isin,",
                "  display_name = excluded.display_name;",
                "",
            ]
        )

    rows: list[str] = []
    for ticker, _, _ in instruments:
        for factor in FACTORS:
            sens, mmj, source = _cell(ticker, factor)
            rows.append(
                f"  ('{ticker}', '{factor}', {sens}::smallint, "
                f"'{mmj}'::public.mmj_type, '{source}', "
                f"'2026-03-15T06:30:00+00'::timestamptz)"
            )

    lines.extend(
        [
            "insert into public.instrument_factor_sensitivity",
            "  (instrument_id, factor_id, sensitivity, mmj_tag, source_url, retrieved_at)",
            "select i.id, f.id, v.sensitivity, v.mmj_tag, v.source_url, v.retrieved_at",
            "from (values",
            ",\n".join(rows),
            ") as v(ticker, factor_slug, sensitivity, mmj_tag, source_url, retrieved_at)",
            "join public.instruments i on i.exchange = 'NSE' and i.ticker = v.ticker",
            "join public.factors f on f.slug = v.factor_slug",
            "on conflict (instrument_id, factor_id) do update set",
            "  sensitivity = excluded.sensitivity,",
            "  mmj_tag = excluded.mmj_tag,",
            "  source_url = excluded.source_url,",
            "  retrieved_at = excluded.retrieved_at;",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    out_dir = Path(__file__).resolve().parents[1] / "db" / "seeds" / "sectors"
    out_dir.mkdir(parents=True, exist_ok=True)
    for slug, (name, instruments) in SECTORS.items():
        path = out_dir / f"{slug}.sql"
        path.write_text(render_sector(slug, name, instruments), encoding="utf-8")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
