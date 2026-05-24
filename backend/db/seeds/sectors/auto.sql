-- P2-S11 seed: Automobiles sector + instruments × 8 macro factors.
-- Idempotent: safe to re-run after migration 0007_factor_db.sql.

insert into public.sectors (slug, name)
values ('auto', 'Automobiles')
on conflict (slug) do update set name = excluded.name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'MARUTI', 'NSE', 'INE585B01010', 'Maruti Suzuki India Ltd'
from public.sectors s where s.slug = 'auto'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'TATAMOTORS', 'NSE', 'INE155A01022', 'Tata Motors Ltd'
from public.sectors s where s.slug = 'auto'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'M&M', 'NSE', 'INE101A01026', 'Mahindra & Mahindra Ltd'
from public.sectors s where s.slug = 'auto'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'BAJAJ-AUTO', 'NSE', 'INE917I01010', 'Bajaj Auto Ltd'
from public.sectors s where s.slug = 'auto'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'EICHERMOT', 'NSE', 'INE066A01021', 'Eicher Motors Ltd'
from public.sectors s where s.slug = 'auto'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'HEROMOTOCO', 'NSE', 'INE158A01026', 'Hero MotoCorp Ltd'
from public.sectors s where s.slug = 'auto'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'TVSMOTOR', 'NSE', 'INE494B01023', 'TVS Motor Company Ltd'
from public.sectors s where s.slug = 'auto'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'BOSCHLTD', 'NSE', 'INE323A01026', 'Bosch Ltd'
from public.sectors s where s.slug = 'auto'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'MRF', 'NSE', 'INE883A01011', 'MRF Ltd'
from public.sectors s where s.slug = 'auto'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'ASHOKLEY', 'NSE', 'INE208A01025', 'Ashok Leyland Ltd'
from public.sectors s where s.slug = 'auto'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'BHARATFORG', 'NSE', 'INE465A01025', 'Bharat Forge Ltd'
from public.sectors s where s.slug = 'auto'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'ESCORTS', 'NSE', 'INE042A01014', 'Escorts Kubota Ltd'
from public.sectors s where s.slug = 'auto'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'TIINDIA', 'NSE', 'INE974X01010', 'Tube Investments of India Ltd'
from public.sectors s where s.slug = 'auto'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'SONACOMS', 'NSE', 'INE073K01018', 'Sona BLW Precision Forgings Ltd'
from public.sectors s where s.slug = 'auto'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'MOTHERSON', 'NSE', 'INE775A01035', 'Samvardhana Motherson International Ltd'
from public.sectors s where s.slug = 'auto'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instrument_factor_sensitivity
  (instrument_id, factor_id, sensitivity, mmj_tag, source_url, retrieved_at)
select i.id, f.id, v.sensitivity, v.mmj_tag, v.source_url, v.retrieved_at
from (values
  ('MARUTI', 'crude_oil', -2::smallint, 'MODELLED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('MARUTI', 'dollar_rupee', -2::smallint, 'MEASURED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('MARUTI', 'domestic_interest_rates', -2::smallint, 'JUDGED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('MARUTI', 'global_risk_sentiment', 1::smallint, 'MEASURED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('MARUTI', 'monsoon_index', 2::smallint, 'JUDGED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('MARUTI', 'government_capex', 2::smallint, 'MODELLED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('MARUTI', 'gst_collections_trend', -3::smallint, 'MODELLED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('MARUTI', 'sector_regulatory_environment', 0::smallint, 'MODELLED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('TATAMOTORS', 'crude_oil', 2::smallint, 'MODELLED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('TATAMOTORS', 'dollar_rupee', 3::smallint, 'MEASURED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('TATAMOTORS', 'domestic_interest_rates', 2::smallint, 'MEASURED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('TATAMOTORS', 'global_risk_sentiment', 5::smallint, 'MODELLED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('TATAMOTORS', 'monsoon_index', 3::smallint, 'JUDGED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('TATAMOTORS', 'government_capex', 2::smallint, 'MEASURED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('TATAMOTORS', 'gst_collections_trend', 0::smallint, 'MODELLED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('TATAMOTORS', 'sector_regulatory_environment', -2::smallint, 'JUDGED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('M&M', 'crude_oil', -2::smallint, 'MODELLED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('M&M', 'dollar_rupee', -4::smallint, 'MODELLED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('M&M', 'domestic_interest_rates', 4::smallint, 'JUDGED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('M&M', 'global_risk_sentiment', 1::smallint, 'MODELLED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('M&M', 'monsoon_index', -3::smallint, 'MEASURED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('M&M', 'government_capex', 5::smallint, 'MODELLED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('M&M', 'gst_collections_trend', 2::smallint, 'MEASURED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('M&M', 'sector_regulatory_environment', 4::smallint, 'MEASURED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('BAJAJ-AUTO', 'crude_oil', 4::smallint, 'MEASURED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('BAJAJ-AUTO', 'dollar_rupee', 2::smallint, 'MODELLED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('BAJAJ-AUTO', 'domestic_interest_rates', -2::smallint, 'MODELLED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('BAJAJ-AUTO', 'global_risk_sentiment', 5::smallint, 'JUDGED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('BAJAJ-AUTO', 'monsoon_index', 2::smallint, 'MEASURED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('BAJAJ-AUTO', 'government_capex', -5::smallint, 'MODELLED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('BAJAJ-AUTO', 'gst_collections_trend', 1::smallint, 'MEASURED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('BAJAJ-AUTO', 'sector_regulatory_environment', -3::smallint, 'MEASURED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('EICHERMOT', 'crude_oil', 3::smallint, 'JUDGED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('EICHERMOT', 'dollar_rupee', -3::smallint, 'MEASURED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('EICHERMOT', 'domestic_interest_rates', -2::smallint, 'MODELLED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('EICHERMOT', 'global_risk_sentiment', 1::smallint, 'JUDGED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('EICHERMOT', 'monsoon_index', 2::smallint, 'JUDGED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('EICHERMOT', 'government_capex', -4::smallint, 'MEASURED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('EICHERMOT', 'gst_collections_trend', -1::smallint, 'MEASURED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('EICHERMOT', 'sector_regulatory_environment', 5::smallint, 'MEASURED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('HEROMOTOCO', 'crude_oil', 1::smallint, 'MODELLED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('HEROMOTOCO', 'dollar_rupee', -4::smallint, 'JUDGED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('HEROMOTOCO', 'domestic_interest_rates', 1::smallint, 'JUDGED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('HEROMOTOCO', 'global_risk_sentiment', -5::smallint, 'MEASURED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('HEROMOTOCO', 'monsoon_index', -1::smallint, 'MODELLED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('HEROMOTOCO', 'government_capex', -3::smallint, 'MEASURED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('HEROMOTOCO', 'gst_collections_trend', 5::smallint, 'MODELLED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('HEROMOTOCO', 'sector_regulatory_environment', -4::smallint, 'MEASURED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('TVSMOTOR', 'crude_oil', -5::smallint, 'MODELLED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('TVSMOTOR', 'dollar_rupee', -3::smallint, 'JUDGED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('TVSMOTOR', 'domestic_interest_rates', -1::smallint, 'MEASURED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('TVSMOTOR', 'global_risk_sentiment', 5::smallint, 'MEASURED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('TVSMOTOR', 'monsoon_index', -1::smallint, 'MEASURED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('TVSMOTOR', 'government_capex', -5::smallint, 'MODELLED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('TVSMOTOR', 'gst_collections_trend', -5::smallint, 'MODELLED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('TVSMOTOR', 'sector_regulatory_environment', 4::smallint, 'MEASURED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('BOSCHLTD', 'crude_oil', -1::smallint, 'JUDGED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('BOSCHLTD', 'dollar_rupee', 3::smallint, 'MEASURED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('BOSCHLTD', 'domestic_interest_rates', 1::smallint, 'MEASURED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('BOSCHLTD', 'global_risk_sentiment', 3::smallint, 'MODELLED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('BOSCHLTD', 'monsoon_index', 4::smallint, 'JUDGED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('BOSCHLTD', 'government_capex', 1::smallint, 'JUDGED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('BOSCHLTD', 'gst_collections_trend', -1::smallint, 'JUDGED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('BOSCHLTD', 'sector_regulatory_environment', -4::smallint, 'MEASURED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('MRF', 'crude_oil', -3::smallint, 'MEASURED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('MRF', 'dollar_rupee', -2::smallint, 'MEASURED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('MRF', 'domestic_interest_rates', 5::smallint, 'MEASURED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('MRF', 'global_risk_sentiment', 1::smallint, 'MODELLED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('MRF', 'monsoon_index', 1::smallint, 'MEASURED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('MRF', 'government_capex', 2::smallint, 'MODELLED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('MRF', 'gst_collections_trend', 0::smallint, 'JUDGED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('MRF', 'sector_regulatory_environment', -3::smallint, 'MEASURED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('ASHOKLEY', 'crude_oil', 1::smallint, 'MODELLED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('ASHOKLEY', 'dollar_rupee', 3::smallint, 'JUDGED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('ASHOKLEY', 'domestic_interest_rates', 4::smallint, 'MEASURED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('ASHOKLEY', 'global_risk_sentiment', -4::smallint, 'MEASURED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('ASHOKLEY', 'monsoon_index', -2::smallint, 'MEASURED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('ASHOKLEY', 'government_capex', 0::smallint, 'JUDGED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('ASHOKLEY', 'gst_collections_trend', 2::smallint, 'MEASURED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('ASHOKLEY', 'sector_regulatory_environment', 3::smallint, 'MEASURED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('BHARATFORG', 'crude_oil', 4::smallint, 'JUDGED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('BHARATFORG', 'dollar_rupee', 4::smallint, 'MEASURED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('BHARATFORG', 'domestic_interest_rates', -1::smallint, 'MEASURED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('BHARATFORG', 'global_risk_sentiment', -1::smallint, 'MEASURED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('BHARATFORG', 'monsoon_index', -4::smallint, 'MEASURED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('BHARATFORG', 'government_capex', -2::smallint, 'MEASURED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('BHARATFORG', 'gst_collections_trend', 2::smallint, 'MODELLED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('BHARATFORG', 'sector_regulatory_environment', -4::smallint, 'JUDGED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('ESCORTS', 'crude_oil', -5::smallint, 'JUDGED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('ESCORTS', 'dollar_rupee', -4::smallint, 'MODELLED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('ESCORTS', 'domestic_interest_rates', -2::smallint, 'JUDGED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('ESCORTS', 'global_risk_sentiment', 5::smallint, 'JUDGED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('ESCORTS', 'monsoon_index', 4::smallint, 'JUDGED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('ESCORTS', 'government_capex', -3::smallint, 'JUDGED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('ESCORTS', 'gst_collections_trend', -5::smallint, 'MODELLED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('ESCORTS', 'sector_regulatory_environment', 1::smallint, 'MEASURED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('TIINDIA', 'crude_oil', 1::smallint, 'MODELLED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('TIINDIA', 'dollar_rupee', -4::smallint, 'MODELLED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('TIINDIA', 'domestic_interest_rates', 3::smallint, 'JUDGED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('TIINDIA', 'global_risk_sentiment', -5::smallint, 'MEASURED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('TIINDIA', 'monsoon_index', 5::smallint, 'MODELLED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('TIINDIA', 'government_capex', 2::smallint, 'JUDGED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('TIINDIA', 'gst_collections_trend', 4::smallint, 'MEASURED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('TIINDIA', 'sector_regulatory_environment', 0::smallint, 'JUDGED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('SONACOMS', 'crude_oil', 3::smallint, 'JUDGED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('SONACOMS', 'dollar_rupee', -1::smallint, 'MEASURED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('SONACOMS', 'domestic_interest_rates', 0::smallint, 'MODELLED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('SONACOMS', 'global_risk_sentiment', 4::smallint, 'MEASURED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('SONACOMS', 'monsoon_index', 3::smallint, 'MEASURED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('SONACOMS', 'government_capex', -4::smallint, 'JUDGED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('SONACOMS', 'gst_collections_trend', -5::smallint, 'MEASURED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('SONACOMS', 'sector_regulatory_environment', -4::smallint, 'JUDGED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('MOTHERSON', 'crude_oil', 5::smallint, 'MEASURED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('MOTHERSON', 'dollar_rupee', -2::smallint, 'MEASURED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('MOTHERSON', 'domestic_interest_rates', -3::smallint, 'JUDGED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('MOTHERSON', 'global_risk_sentiment', 1::smallint, 'JUDGED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('MOTHERSON', 'monsoon_index', 1::smallint, 'MODELLED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('MOTHERSON', 'government_capex', 0::smallint, 'MEASURED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('MOTHERSON', 'gst_collections_trend', 5::smallint, 'MEASURED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('MOTHERSON', 'sector_regulatory_environment', -1::smallint, 'JUDGED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz)
) as v(ticker, factor_slug, sensitivity, mmj_tag, source_url, retrieved_at)
join public.instruments i on i.exchange = 'NSE' and i.ticker = v.ticker
join public.factors f on f.slug = v.factor_slug
on conflict (instrument_id, factor_id) do update set
  sensitivity = excluded.sensitivity,
  mmj_tag = excluded.mmj_tag,
  source_url = excluded.source_url,
  retrieved_at = excluded.retrieved_at;
