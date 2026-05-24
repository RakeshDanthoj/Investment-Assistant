-- P2-S11 seed: Information Technology sector + instruments × 8 macro factors.
-- Idempotent: safe to re-run after migration 0007_factor_db.sql.

insert into public.sectors (slug, name)
values ('it', 'Information Technology')
on conflict (slug) do update set name = excluded.name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'TCS', 'NSE', 'INE467B01029', 'Tata Consultancy Services Ltd'
from public.sectors s where s.slug = 'it'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'INFY', 'NSE', 'INE009A01021', 'Infosys Ltd'
from public.sectors s where s.slug = 'it'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'HCLTECH', 'NSE', 'INE860A01027', 'HCL Technologies Ltd'
from public.sectors s where s.slug = 'it'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'WIPRO', 'NSE', 'INE075A01022', 'Wipro Ltd'
from public.sectors s where s.slug = 'it'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'TECHM', 'NSE', 'INE669C01036', 'Tech Mahindra Ltd'
from public.sectors s where s.slug = 'it'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'LTIM', 'NSE', 'INE214T01019', 'LTIMindtree Ltd'
from public.sectors s where s.slug = 'it'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'PERSISTENT', 'NSE', 'INE262H01021', 'Persistent Systems Ltd'
from public.sectors s where s.slug = 'it'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'COFORGE', 'NSE', 'INE591G01025', 'Coforge Ltd'
from public.sectors s where s.slug = 'it'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'MPHASIS', 'NSE', 'INE356A01018', 'Mphasis Ltd'
from public.sectors s where s.slug = 'it'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'LTTS', 'NSE', 'INE010V01017', 'L&T Technology Services Ltd'
from public.sectors s where s.slug = 'it'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'TATAELXSI', 'NSE', 'INE670A01012', 'Tata Elxsi Ltd'
from public.sectors s where s.slug = 'it'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'KPITTECH', 'NSE', 'INE04I401011', 'KPIT Technologies Ltd'
from public.sectors s where s.slug = 'it'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'HAPPSTMNDS', 'NSE', 'INE419U01012', 'Happiest Minds Technologies Ltd'
from public.sectors s where s.slug = 'it'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'OFSS', 'NSE', 'INE881D01047', 'Oracle Financial Services Software Ltd'
from public.sectors s where s.slug = 'it'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'CIGNITITEC', 'NSE', 'INE675C01017', 'Cigniti Technologies Ltd'
from public.sectors s where s.slug = 'it'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instrument_factor_sensitivity
  (instrument_id, factor_id, sensitivity, mmj_tag, source_url, retrieved_at)
select i.id, f.id, v.sensitivity, v.mmj_tag, v.source_url, v.retrieved_at
from (values
  ('TCS', 'crude_oil', 0::smallint, 'MODELLED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('TCS', 'dollar_rupee', -5::smallint, 'MEASURED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('TCS', 'domestic_interest_rates', 2::smallint, 'MODELLED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('TCS', 'global_risk_sentiment', -2::smallint, 'JUDGED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('TCS', 'monsoon_index', 3::smallint, 'MODELLED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('TCS', 'government_capex', 0::smallint, 'JUDGED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('TCS', 'gst_collections_trend', 5::smallint, 'MEASURED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('TCS', 'sector_regulatory_environment', 0::smallint, 'MEASURED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('INFY', 'crude_oil', -5::smallint, 'MEASURED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('INFY', 'dollar_rupee', 4::smallint, 'MEASURED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('INFY', 'domestic_interest_rates', -3::smallint, 'JUDGED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('INFY', 'global_risk_sentiment', 2::smallint, 'JUDGED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('INFY', 'monsoon_index', 0::smallint, 'MODELLED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('INFY', 'government_capex', 2::smallint, 'MEASURED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('INFY', 'gst_collections_trend', 1::smallint, 'JUDGED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('INFY', 'sector_regulatory_environment', -1::smallint, 'JUDGED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('HCLTECH', 'crude_oil', -4::smallint, 'JUDGED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('HCLTECH', 'dollar_rupee', -2::smallint, 'JUDGED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('HCLTECH', 'domestic_interest_rates', 1::smallint, 'MEASURED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('HCLTECH', 'global_risk_sentiment', -2::smallint, 'JUDGED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('HCLTECH', 'monsoon_index', -2::smallint, 'JUDGED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('HCLTECH', 'government_capex', -4::smallint, 'MEASURED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('HCLTECH', 'gst_collections_trend', 0::smallint, 'MODELLED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('HCLTECH', 'sector_regulatory_environment', 2::smallint, 'MEASURED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('WIPRO', 'crude_oil', -4::smallint, 'JUDGED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('WIPRO', 'dollar_rupee', -2::smallint, 'MODELLED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('WIPRO', 'domestic_interest_rates', -3::smallint, 'MODELLED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('WIPRO', 'global_risk_sentiment', 0::smallint, 'MODELLED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('WIPRO', 'monsoon_index', -4::smallint, 'MODELLED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('WIPRO', 'government_capex', -1::smallint, 'MEASURED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('WIPRO', 'gst_collections_trend', 1::smallint, 'JUDGED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('WIPRO', 'sector_regulatory_environment', 3::smallint, 'MEASURED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('TECHM', 'crude_oil', 3::smallint, 'MODELLED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('TECHM', 'dollar_rupee', 3::smallint, 'MODELLED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('TECHM', 'domestic_interest_rates', -5::smallint, 'JUDGED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('TECHM', 'global_risk_sentiment', 2::smallint, 'MEASURED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('TECHM', 'monsoon_index', 1::smallint, 'MODELLED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('TECHM', 'government_capex', -4::smallint, 'MODELLED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('TECHM', 'gst_collections_trend', -3::smallint, 'MEASURED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('TECHM', 'sector_regulatory_environment', 3::smallint, 'JUDGED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('LTIM', 'crude_oil', 0::smallint, 'JUDGED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('LTIM', 'dollar_rupee', 4::smallint, 'JUDGED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('LTIM', 'domestic_interest_rates', 5::smallint, 'JUDGED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('LTIM', 'global_risk_sentiment', 3::smallint, 'MEASURED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('LTIM', 'monsoon_index', 1::smallint, 'MODELLED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('LTIM', 'government_capex', -3::smallint, 'MODELLED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('LTIM', 'gst_collections_trend', -3::smallint, 'JUDGED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('LTIM', 'sector_regulatory_environment', 5::smallint, 'MEASURED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('PERSISTENT', 'crude_oil', 2::smallint, 'JUDGED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('PERSISTENT', 'dollar_rupee', 5::smallint, 'MODELLED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('PERSISTENT', 'domestic_interest_rates', 0::smallint, 'JUDGED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('PERSISTENT', 'global_risk_sentiment', 0::smallint, 'MODELLED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('PERSISTENT', 'monsoon_index', 2::smallint, 'MEASURED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('PERSISTENT', 'government_capex', -1::smallint, 'MODELLED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('PERSISTENT', 'gst_collections_trend', 4::smallint, 'MEASURED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('PERSISTENT', 'sector_regulatory_environment', 2::smallint, 'MODELLED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('COFORGE', 'crude_oil', -5::smallint, 'MODELLED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('COFORGE', 'dollar_rupee', -5::smallint, 'MODELLED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('COFORGE', 'domestic_interest_rates', 1::smallint, 'MODELLED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('COFORGE', 'global_risk_sentiment', 2::smallint, 'MEASURED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('COFORGE', 'monsoon_index', -4::smallint, 'MEASURED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('COFORGE', 'government_capex', 1::smallint, 'MEASURED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('COFORGE', 'gst_collections_trend', 3::smallint, 'MEASURED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('COFORGE', 'sector_regulatory_environment', -3::smallint, 'MODELLED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('MPHASIS', 'crude_oil', 1::smallint, 'JUDGED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('MPHASIS', 'dollar_rupee', 4::smallint, 'MEASURED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('MPHASIS', 'domestic_interest_rates', 3::smallint, 'JUDGED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('MPHASIS', 'global_risk_sentiment', 2::smallint, 'JUDGED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('MPHASIS', 'monsoon_index', -1::smallint, 'MODELLED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('MPHASIS', 'government_capex', 3::smallint, 'MODELLED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('MPHASIS', 'gst_collections_trend', -3::smallint, 'MODELLED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('MPHASIS', 'sector_regulatory_environment', 4::smallint, 'MODELLED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('LTTS', 'crude_oil', 3::smallint, 'MODELLED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('LTTS', 'dollar_rupee', 3::smallint, 'MODELLED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('LTTS', 'domestic_interest_rates', 0::smallint, 'JUDGED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('LTTS', 'global_risk_sentiment', 4::smallint, 'MODELLED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('LTTS', 'monsoon_index', 4::smallint, 'MEASURED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('LTTS', 'government_capex', 3::smallint, 'JUDGED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('LTTS', 'gst_collections_trend', 4::smallint, 'MEASURED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('LTTS', 'sector_regulatory_environment', 1::smallint, 'MODELLED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('TATAELXSI', 'crude_oil', 3::smallint, 'MEASURED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('TATAELXSI', 'dollar_rupee', -4::smallint, 'MODELLED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('TATAELXSI', 'domestic_interest_rates', 1::smallint, 'JUDGED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('TATAELXSI', 'global_risk_sentiment', 0::smallint, 'MEASURED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('TATAELXSI', 'monsoon_index', 5::smallint, 'MODELLED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('TATAELXSI', 'government_capex', -4::smallint, 'JUDGED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('TATAELXSI', 'gst_collections_trend', -5::smallint, 'MEASURED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('TATAELXSI', 'sector_regulatory_environment', -1::smallint, 'MEASURED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('KPITTECH', 'crude_oil', -5::smallint, 'MODELLED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('KPITTECH', 'dollar_rupee', -2::smallint, 'JUDGED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('KPITTECH', 'domestic_interest_rates', -5::smallint, 'MEASURED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('KPITTECH', 'global_risk_sentiment', 2::smallint, 'MODELLED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('KPITTECH', 'monsoon_index', 0::smallint, 'MEASURED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('KPITTECH', 'government_capex', -1::smallint, 'JUDGED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('KPITTECH', 'gst_collections_trend', -1::smallint, 'JUDGED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('KPITTECH', 'sector_regulatory_environment', 5::smallint, 'JUDGED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('HAPPSTMNDS', 'crude_oil', 1::smallint, 'MEASURED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('HAPPSTMNDS', 'dollar_rupee', 2::smallint, 'JUDGED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('HAPPSTMNDS', 'domestic_interest_rates', 5::smallint, 'MODELLED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('HAPPSTMNDS', 'global_risk_sentiment', -2::smallint, 'JUDGED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('HAPPSTMNDS', 'monsoon_index', -2::smallint, 'MEASURED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('HAPPSTMNDS', 'government_capex', -5::smallint, 'JUDGED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('HAPPSTMNDS', 'gst_collections_trend', -3::smallint, 'MEASURED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('HAPPSTMNDS', 'sector_regulatory_environment', 1::smallint, 'JUDGED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('OFSS', 'crude_oil', 4::smallint, 'MODELLED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('OFSS', 'dollar_rupee', 0::smallint, 'MEASURED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('OFSS', 'domestic_interest_rates', -2::smallint, 'MODELLED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('OFSS', 'global_risk_sentiment', -1::smallint, 'JUDGED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('OFSS', 'monsoon_index', 2::smallint, 'JUDGED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('OFSS', 'government_capex', -3::smallint, 'MODELLED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('OFSS', 'gst_collections_trend', 4::smallint, 'MODELLED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('OFSS', 'sector_regulatory_environment', 1::smallint, 'JUDGED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('CIGNITITEC', 'crude_oil', -1::smallint, 'MODELLED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('CIGNITITEC', 'dollar_rupee', -5::smallint, 'MEASURED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('CIGNITITEC', 'domestic_interest_rates', -4::smallint, 'MODELLED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('CIGNITITEC', 'global_risk_sentiment', 2::smallint, 'JUDGED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('CIGNITITEC', 'monsoon_index', 1::smallint, 'MODELLED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('CIGNITITEC', 'government_capex', 3::smallint, 'MEASURED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('CIGNITITEC', 'gst_collections_trend', 5::smallint, 'MEASURED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('CIGNITITEC', 'sector_regulatory_environment', -2::smallint, 'MODELLED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz)
) as v(ticker, factor_slug, sensitivity, mmj_tag, source_url, retrieved_at)
join public.instruments i on i.exchange = 'NSE' and i.ticker = v.ticker
join public.factors f on f.slug = v.factor_slug
on conflict (instrument_id, factor_id) do update set
  sensitivity = excluded.sensitivity,
  mmj_tag = excluded.mmj_tag,
  source_url = excluded.source_url,
  retrieved_at = excluded.retrieved_at;
