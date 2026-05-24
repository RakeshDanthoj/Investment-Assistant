-- P2-S11 seed: Metals & Materials sector + instruments × 8 macro factors.
-- Idempotent: safe to re-run after migration 0007_factor_db.sql.

insert into public.sectors (slug, name)
values ('metals', 'Metals & Materials')
on conflict (slug) do update set name = excluded.name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'TATASTEEL', 'NSE', 'INE081A01020', 'Tata Steel Ltd'
from public.sectors s where s.slug = 'metals'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'JSWSTEEL', 'NSE', 'INE019A01038', 'JSW Steel Ltd'
from public.sectors s where s.slug = 'metals'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'HINDALCO', 'NSE', 'INE038A01020', 'Hindalco Industries Ltd'
from public.sectors s where s.slug = 'metals'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'VEDL', 'NSE', 'INE205A01025', 'Vedanta Ltd'
from public.sectors s where s.slug = 'metals'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'NMDC', 'NSE', 'INE584A01023', 'NMDC Ltd'
from public.sectors s where s.slug = 'metals'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'SAIL', 'NSE', 'INE114A01011', 'Steel Authority of India Ltd'
from public.sectors s where s.slug = 'metals'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'JINDALSTEL', 'NSE', 'INE749A01030', 'Jindal Steel Ltd'
from public.sectors s where s.slug = 'metals'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'NATIONALUM', 'NSE', 'INE139A01034', 'National Aluminium Company Ltd'
from public.sectors s where s.slug = 'metals'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'HINDZINC', 'NSE', 'INE267A01025', 'Hindustan Zinc Ltd'
from public.sectors s where s.slug = 'metals'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'APLAPOLLO', 'NSE', 'INE702C01027', 'APL Apollo Tubes Ltd'
from public.sectors s where s.slug = 'metals'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'WELCORP', 'NSE', 'INE191B01025', 'Welspun Corp Ltd'
from public.sectors s where s.slug = 'metals'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'RATNAMANI', 'NSE', 'INE703C01027', 'Ratnamani Metals & Tubes Ltd'
from public.sectors s where s.slug = 'metals'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'JSL', 'NSE', 'INE220G01021', 'Jindal Stainless Ltd'
from public.sectors s where s.slug = 'metals'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'HINDCOPPER', 'NSE', 'INE531E01026', 'Hindustan Copper Ltd'
from public.sectors s where s.slug = 'metals'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'MOIL', 'NSE', 'INE490G01020', 'MOIL Ltd'
from public.sectors s where s.slug = 'metals'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instrument_factor_sensitivity
  (instrument_id, factor_id, sensitivity, mmj_tag, source_url, retrieved_at)
select i.id, f.id, v.sensitivity, v.mmj_tag, v.source_url, v.retrieved_at
from (values
  ('TATASTEEL', 'crude_oil', -2::smallint, 'MEASURED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('TATASTEEL', 'dollar_rupee', 3::smallint, 'JUDGED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('TATASTEEL', 'domestic_interest_rates', -2::smallint, 'MEASURED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('TATASTEEL', 'global_risk_sentiment', -2::smallint, 'MEASURED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('TATASTEEL', 'monsoon_index', 3::smallint, 'MEASURED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('TATASTEEL', 'government_capex', -4::smallint, 'JUDGED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('TATASTEEL', 'gst_collections_trend', 0::smallint, 'MEASURED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('TATASTEEL', 'sector_regulatory_environment', 1::smallint, 'MODELLED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('JSWSTEEL', 'crude_oil', 0::smallint, 'JUDGED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('JSWSTEEL', 'dollar_rupee', 4::smallint, 'JUDGED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('JSWSTEEL', 'domestic_interest_rates', 1::smallint, 'MODELLED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('JSWSTEEL', 'global_risk_sentiment', 5::smallint, 'JUDGED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('JSWSTEEL', 'monsoon_index', 3::smallint, 'MODELLED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('JSWSTEEL', 'government_capex', 4::smallint, 'JUDGED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('JSWSTEEL', 'gst_collections_trend', 3::smallint, 'MEASURED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('JSWSTEEL', 'sector_regulatory_environment', 4::smallint, 'MODELLED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('HINDALCO', 'crude_oil', 3::smallint, 'MODELLED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('HINDALCO', 'dollar_rupee', 5::smallint, 'MEASURED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('HINDALCO', 'domestic_interest_rates', -4::smallint, 'MODELLED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('HINDALCO', 'global_risk_sentiment', -3::smallint, 'JUDGED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('HINDALCO', 'monsoon_index', 1::smallint, 'MODELLED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('HINDALCO', 'government_capex', -3::smallint, 'MODELLED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('HINDALCO', 'gst_collections_trend', -3::smallint, 'JUDGED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('HINDALCO', 'sector_regulatory_environment', -1::smallint, 'JUDGED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('VEDL', 'crude_oil', 1::smallint, 'MEASURED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('VEDL', 'dollar_rupee', 0::smallint, 'MODELLED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('VEDL', 'domestic_interest_rates', 3::smallint, 'MODELLED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('VEDL', 'global_risk_sentiment', -3::smallint, 'MEASURED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('VEDL', 'monsoon_index', -2::smallint, 'MEASURED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('VEDL', 'government_capex', 1::smallint, 'MODELLED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('VEDL', 'gst_collections_trend', 4::smallint, 'JUDGED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('VEDL', 'sector_regulatory_environment', 4::smallint, 'MEASURED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('NMDC', 'crude_oil', 2::smallint, 'JUDGED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('NMDC', 'dollar_rupee', 4::smallint, 'MODELLED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('NMDC', 'domestic_interest_rates', -1::smallint, 'MEASURED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('NMDC', 'global_risk_sentiment', -5::smallint, 'MODELLED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('NMDC', 'monsoon_index', -4::smallint, 'JUDGED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('NMDC', 'government_capex', -5::smallint, 'JUDGED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('NMDC', 'gst_collections_trend', 4::smallint, 'JUDGED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('NMDC', 'sector_regulatory_environment', 0::smallint, 'JUDGED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('SAIL', 'crude_oil', -4::smallint, 'JUDGED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('SAIL', 'dollar_rupee', -1::smallint, 'MODELLED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('SAIL', 'domestic_interest_rates', -3::smallint, 'MODELLED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('SAIL', 'global_risk_sentiment', 5::smallint, 'MODELLED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('SAIL', 'monsoon_index', 2::smallint, 'JUDGED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('SAIL', 'government_capex', -4::smallint, 'JUDGED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('SAIL', 'gst_collections_trend', -3::smallint, 'JUDGED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('SAIL', 'sector_regulatory_environment', -5::smallint, 'JUDGED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('JINDALSTEL', 'crude_oil', -1::smallint, 'MODELLED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('JINDALSTEL', 'dollar_rupee', 0::smallint, 'MODELLED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('JINDALSTEL', 'domestic_interest_rates', 5::smallint, 'MODELLED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('JINDALSTEL', 'global_risk_sentiment', 1::smallint, 'MODELLED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('JINDALSTEL', 'monsoon_index', -1::smallint, 'MODELLED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('JINDALSTEL', 'government_capex', -4::smallint, 'JUDGED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('JINDALSTEL', 'gst_collections_trend', 0::smallint, 'MEASURED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('JINDALSTEL', 'sector_regulatory_environment', -2::smallint, 'MODELLED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('NATIONALUM', 'crude_oil', -5::smallint, 'MODELLED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('NATIONALUM', 'dollar_rupee', -4::smallint, 'JUDGED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('NATIONALUM', 'domestic_interest_rates', 1::smallint, 'MODELLED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('NATIONALUM', 'global_risk_sentiment', -4::smallint, 'MODELLED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('NATIONALUM', 'monsoon_index', -5::smallint, 'MEASURED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('NATIONALUM', 'government_capex', -1::smallint, 'JUDGED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('NATIONALUM', 'gst_collections_trend', 5::smallint, 'MEASURED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('NATIONALUM', 'sector_regulatory_environment', 4::smallint, 'JUDGED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('HINDZINC', 'crude_oil', -1::smallint, 'MEASURED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('HINDZINC', 'dollar_rupee', 2::smallint, 'JUDGED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('HINDZINC', 'domestic_interest_rates', 3::smallint, 'MODELLED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('HINDZINC', 'global_risk_sentiment', 2::smallint, 'MEASURED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('HINDZINC', 'monsoon_index', -5::smallint, 'JUDGED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('HINDZINC', 'government_capex', 1::smallint, 'MEASURED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('HINDZINC', 'gst_collections_trend', 2::smallint, 'JUDGED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('HINDZINC', 'sector_regulatory_environment', -3::smallint, 'MODELLED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('APLAPOLLO', 'crude_oil', 4::smallint, 'JUDGED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('APLAPOLLO', 'dollar_rupee', -1::smallint, 'JUDGED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('APLAPOLLO', 'domestic_interest_rates', -3::smallint, 'MEASURED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('APLAPOLLO', 'global_risk_sentiment', 3::smallint, 'MODELLED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('APLAPOLLO', 'monsoon_index', 2::smallint, 'JUDGED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('APLAPOLLO', 'government_capex', 2::smallint, 'JUDGED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('APLAPOLLO', 'gst_collections_trend', 2::smallint, 'JUDGED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('APLAPOLLO', 'sector_regulatory_environment', 3::smallint, 'JUDGED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('WELCORP', 'crude_oil', -5::smallint, 'MEASURED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('WELCORP', 'dollar_rupee', 3::smallint, 'MEASURED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('WELCORP', 'domestic_interest_rates', 1::smallint, 'MEASURED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('WELCORP', 'global_risk_sentiment', 3::smallint, 'JUDGED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('WELCORP', 'monsoon_index', 5::smallint, 'MODELLED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('WELCORP', 'government_capex', -3::smallint, 'MODELLED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('WELCORP', 'gst_collections_trend', 1::smallint, 'JUDGED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('WELCORP', 'sector_regulatory_environment', -1::smallint, 'JUDGED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('RATNAMANI', 'crude_oil', -2::smallint, 'MEASURED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('RATNAMANI', 'dollar_rupee', 0::smallint, 'JUDGED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('RATNAMANI', 'domestic_interest_rates', -4::smallint, 'JUDGED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('RATNAMANI', 'global_risk_sentiment', 4::smallint, 'JUDGED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('RATNAMANI', 'monsoon_index', -5::smallint, 'MEASURED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('RATNAMANI', 'government_capex', -4::smallint, 'JUDGED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('RATNAMANI', 'gst_collections_trend', 4::smallint, 'MODELLED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('RATNAMANI', 'sector_regulatory_environment', 5::smallint, 'JUDGED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('JSL', 'crude_oil', 4::smallint, 'MEASURED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('JSL', 'dollar_rupee', 4::smallint, 'MODELLED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('JSL', 'domestic_interest_rates', 2::smallint, 'MEASURED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('JSL', 'global_risk_sentiment', 2::smallint, 'MEASURED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('JSL', 'monsoon_index', -2::smallint, 'MEASURED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('JSL', 'government_capex', -4::smallint, 'JUDGED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('JSL', 'gst_collections_trend', -4::smallint, 'JUDGED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('JSL', 'sector_regulatory_environment', -3::smallint, 'MODELLED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('HINDCOPPER', 'crude_oil', -2::smallint, 'JUDGED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('HINDCOPPER', 'dollar_rupee', 2::smallint, 'MODELLED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('HINDCOPPER', 'domestic_interest_rates', 2::smallint, 'JUDGED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('HINDCOPPER', 'global_risk_sentiment', -4::smallint, 'MODELLED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('HINDCOPPER', 'monsoon_index', -4::smallint, 'MODELLED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('HINDCOPPER', 'government_capex', -2::smallint, 'MEASURED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('HINDCOPPER', 'gst_collections_trend', -3::smallint, 'MEASURED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('HINDCOPPER', 'sector_regulatory_environment', 2::smallint, 'MODELLED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('MOIL', 'crude_oil', -2::smallint, 'MEASURED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('MOIL', 'dollar_rupee', 5::smallint, 'MEASURED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('MOIL', 'domestic_interest_rates', 0::smallint, 'JUDGED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('MOIL', 'global_risk_sentiment', -5::smallint, 'JUDGED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('MOIL', 'monsoon_index', 3::smallint, 'JUDGED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('MOIL', 'government_capex', 2::smallint, 'MEASURED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('MOIL', 'gst_collections_trend', -1::smallint, 'MEASURED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('MOIL', 'sector_regulatory_environment', 5::smallint, 'MEASURED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz)
) as v(ticker, factor_slug, sensitivity, mmj_tag, source_url, retrieved_at)
join public.instruments i on i.exchange = 'NSE' and i.ticker = v.ticker
join public.factors f on f.slug = v.factor_slug
on conflict (instrument_id, factor_id) do update set
  sensitivity = excluded.sensitivity,
  mmj_tag = excluded.mmj_tag,
  source_url = excluded.source_url,
  retrieved_at = excluded.retrieved_at;
