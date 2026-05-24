-- P2-S11 seed: Telecommunications sector + instruments × 8 macro factors.
-- Idempotent: safe to re-run after migration 0007_factor_db.sql.

insert into public.sectors (slug, name)
values ('telecom', 'Telecommunications')
on conflict (slug) do update set name = excluded.name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'BHARTIARTL', 'NSE', 'INE397D01024', 'Bharti Airtel Ltd'
from public.sectors s where s.slug = 'telecom'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'IDEA', 'NSE', 'INE669E01016', 'Vodafone Idea Ltd'
from public.sectors s where s.slug = 'telecom'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'INDUSTOWER', 'NSE', 'INE121J01017', 'Indus Towers Ltd'
from public.sectors s where s.slug = 'telecom'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'TATACOMM', 'NSE', 'INE151A01013', 'Tata Communications Ltd'
from public.sectors s where s.slug = 'telecom'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'RAILTEL', 'NSE', 'INE0DD101019', 'RailTel Corporation of India Ltd'
from public.sectors s where s.slug = 'telecom'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'HFCL', 'NSE', 'INE548A01028', 'HFCL Ltd'
from public.sectors s where s.slug = 'telecom'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'TEJASNET', 'NSE', 'INE010J01012', 'Tejas Networks Ltd'
from public.sectors s where s.slug = 'telecom'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'ROUTE', 'NSE', 'INE450U01017', 'Route Mobile Ltd'
from public.sectors s where s.slug = 'telecom'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'STLTECH', 'NSE', 'INE089C01029', 'Sterlite Technologies Ltd'
from public.sectors s where s.slug = 'telecom'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'ITI', 'NSE', 'INE248A01017', 'ITI Ltd'
from public.sectors s where s.slug = 'telecom'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'GTLINFRA', 'NSE', 'INE869I01013', 'GTL Infrastructure Ltd'
from public.sectors s where s.slug = 'telecom'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'DATAPATTNS', 'NSE', 'INE0DZJ01015', 'Data Patterns (India) Ltd'
from public.sectors s where s.slug = 'telecom'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'BBOX', 'NSE', 'INE676A01027', 'Black Box Ltd'
from public.sectors s where s.slug = 'telecom'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'NUVAMA', 'NSE', 'INE531F01054', 'Nuvama Wealth Management Ltd'
from public.sectors s where s.slug = 'telecom'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'MTNL', 'NSE', 'INE153A01019', 'Mahanagar Telephone Nigam Ltd'
from public.sectors s where s.slug = 'telecom'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instrument_factor_sensitivity
  (instrument_id, factor_id, sensitivity, mmj_tag, source_url, retrieved_at)
select i.id, f.id, v.sensitivity, v.mmj_tag, v.source_url, v.retrieved_at
from (values
  ('BHARTIARTL', 'crude_oil', 2::smallint, 'JUDGED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('BHARTIARTL', 'dollar_rupee', 1::smallint, 'MEASURED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('BHARTIARTL', 'domestic_interest_rates', -4::smallint, 'MEASURED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('BHARTIARTL', 'global_risk_sentiment', 2::smallint, 'JUDGED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('BHARTIARTL', 'monsoon_index', 3::smallint, 'MEASURED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('BHARTIARTL', 'government_capex', 4::smallint, 'MODELLED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('BHARTIARTL', 'gst_collections_trend', -3::smallint, 'MODELLED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('BHARTIARTL', 'sector_regulatory_environment', 3::smallint, 'JUDGED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('IDEA', 'crude_oil', 2::smallint, 'JUDGED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('IDEA', 'dollar_rupee', -1::smallint, 'MODELLED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('IDEA', 'domestic_interest_rates', -1::smallint, 'MODELLED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('IDEA', 'global_risk_sentiment', -1::smallint, 'JUDGED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('IDEA', 'monsoon_index', 2::smallint, 'JUDGED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('IDEA', 'government_capex', -5::smallint, 'JUDGED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('IDEA', 'gst_collections_trend', -3::smallint, 'MODELLED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('IDEA', 'sector_regulatory_environment', -1::smallint, 'JUDGED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('INDUSTOWER', 'crude_oil', 3::smallint, 'MEASURED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('INDUSTOWER', 'dollar_rupee', -1::smallint, 'MEASURED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('INDUSTOWER', 'domestic_interest_rates', 3::smallint, 'JUDGED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('INDUSTOWER', 'global_risk_sentiment', 4::smallint, 'MEASURED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('INDUSTOWER', 'monsoon_index', 3::smallint, 'MEASURED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('INDUSTOWER', 'government_capex', -3::smallint, 'MODELLED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('INDUSTOWER', 'gst_collections_trend', 3::smallint, 'MODELLED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('INDUSTOWER', 'sector_regulatory_environment', -2::smallint, 'MEASURED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('TATACOMM', 'crude_oil', -3::smallint, 'JUDGED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('TATACOMM', 'dollar_rupee', 3::smallint, 'MODELLED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('TATACOMM', 'domestic_interest_rates', 4::smallint, 'MODELLED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('TATACOMM', 'global_risk_sentiment', 0::smallint, 'MODELLED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('TATACOMM', 'monsoon_index', 3::smallint, 'MODELLED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('TATACOMM', 'government_capex', -1::smallint, 'MODELLED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('TATACOMM', 'gst_collections_trend', 1::smallint, 'MEASURED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('TATACOMM', 'sector_regulatory_environment', -4::smallint, 'JUDGED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('RAILTEL', 'crude_oil', 0::smallint, 'JUDGED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('RAILTEL', 'dollar_rupee', 0::smallint, 'MODELLED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('RAILTEL', 'domestic_interest_rates', 5::smallint, 'MODELLED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('RAILTEL', 'global_risk_sentiment', 3::smallint, 'MEASURED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('RAILTEL', 'monsoon_index', 3::smallint, 'JUDGED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('RAILTEL', 'government_capex', -3::smallint, 'MODELLED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('RAILTEL', 'gst_collections_trend', 3::smallint, 'JUDGED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('RAILTEL', 'sector_regulatory_environment', -3::smallint, 'MODELLED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('HFCL', 'crude_oil', -3::smallint, 'JUDGED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('HFCL', 'dollar_rupee', 2::smallint, 'MODELLED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('HFCL', 'domestic_interest_rates', 0::smallint, 'JUDGED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('HFCL', 'global_risk_sentiment', -5::smallint, 'MEASURED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('HFCL', 'monsoon_index', -3::smallint, 'JUDGED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('HFCL', 'government_capex', -5::smallint, 'MEASURED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('HFCL', 'gst_collections_trend', -2::smallint, 'MEASURED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('HFCL', 'sector_regulatory_environment', -3::smallint, 'JUDGED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('TEJASNET', 'crude_oil', 1::smallint, 'MEASURED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('TEJASNET', 'dollar_rupee', -1::smallint, 'JUDGED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('TEJASNET', 'domestic_interest_rates', -2::smallint, 'MEASURED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('TEJASNET', 'global_risk_sentiment', 4::smallint, 'JUDGED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('TEJASNET', 'monsoon_index', 0::smallint, 'JUDGED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('TEJASNET', 'government_capex', -4::smallint, 'MEASURED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('TEJASNET', 'gst_collections_trend', 0::smallint, 'JUDGED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('TEJASNET', 'sector_regulatory_environment', 0::smallint, 'MODELLED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('ROUTE', 'crude_oil', 5::smallint, 'MEASURED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('ROUTE', 'dollar_rupee', 0::smallint, 'JUDGED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('ROUTE', 'domestic_interest_rates', 2::smallint, 'JUDGED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('ROUTE', 'global_risk_sentiment', -1::smallint, 'MODELLED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('ROUTE', 'monsoon_index', -3::smallint, 'JUDGED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('ROUTE', 'government_capex', -1::smallint, 'JUDGED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('ROUTE', 'gst_collections_trend', 0::smallint, 'MEASURED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('ROUTE', 'sector_regulatory_environment', -2::smallint, 'JUDGED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('STLTECH', 'crude_oil', 2::smallint, 'MODELLED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('STLTECH', 'dollar_rupee', -5::smallint, 'MEASURED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('STLTECH', 'domestic_interest_rates', 0::smallint, 'JUDGED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('STLTECH', 'global_risk_sentiment', -4::smallint, 'MEASURED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('STLTECH', 'monsoon_index', 3::smallint, 'JUDGED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('STLTECH', 'government_capex', 4::smallint, 'JUDGED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('STLTECH', 'gst_collections_trend', 1::smallint, 'MEASURED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('STLTECH', 'sector_regulatory_environment', 1::smallint, 'MEASURED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('ITI', 'crude_oil', 4::smallint, 'MEASURED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('ITI', 'dollar_rupee', 0::smallint, 'MEASURED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('ITI', 'domestic_interest_rates', 5::smallint, 'MEASURED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('ITI', 'global_risk_sentiment', 1::smallint, 'JUDGED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('ITI', 'monsoon_index', 0::smallint, 'MODELLED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('ITI', 'government_capex', 3::smallint, 'MODELLED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('ITI', 'gst_collections_trend', 2::smallint, 'JUDGED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('ITI', 'sector_regulatory_environment', 2::smallint, 'MEASURED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('GTLINFRA', 'crude_oil', 1::smallint, 'MEASURED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('GTLINFRA', 'dollar_rupee', 2::smallint, 'JUDGED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('GTLINFRA', 'domestic_interest_rates', 3::smallint, 'MODELLED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('GTLINFRA', 'global_risk_sentiment', 1::smallint, 'MODELLED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('GTLINFRA', 'monsoon_index', 4::smallint, 'MODELLED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('GTLINFRA', 'government_capex', 0::smallint, 'MEASURED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('GTLINFRA', 'gst_collections_trend', 5::smallint, 'JUDGED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('GTLINFRA', 'sector_regulatory_environment', -2::smallint, 'MEASURED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('DATAPATTNS', 'crude_oil', -3::smallint, 'MEASURED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('DATAPATTNS', 'dollar_rupee', 2::smallint, 'JUDGED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('DATAPATTNS', 'domestic_interest_rates', 1::smallint, 'MODELLED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('DATAPATTNS', 'global_risk_sentiment', -5::smallint, 'MEASURED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('DATAPATTNS', 'monsoon_index', 3::smallint, 'JUDGED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('DATAPATTNS', 'government_capex', 4::smallint, 'JUDGED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('DATAPATTNS', 'gst_collections_trend', -4::smallint, 'JUDGED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('DATAPATTNS', 'sector_regulatory_environment', 4::smallint, 'MEASURED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('BBOX', 'crude_oil', -2::smallint, 'JUDGED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('BBOX', 'dollar_rupee', 4::smallint, 'MODELLED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('BBOX', 'domestic_interest_rates', 0::smallint, 'JUDGED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('BBOX', 'global_risk_sentiment', 0::smallint, 'MEASURED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('BBOX', 'monsoon_index', -2::smallint, 'MEASURED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('BBOX', 'government_capex', -4::smallint, 'MEASURED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('BBOX', 'gst_collections_trend', -3::smallint, 'MEASURED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('BBOX', 'sector_regulatory_environment', -1::smallint, 'MODELLED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('NUVAMA', 'crude_oil', -3::smallint, 'JUDGED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('NUVAMA', 'dollar_rupee', 2::smallint, 'JUDGED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('NUVAMA', 'domestic_interest_rates', 5::smallint, 'MODELLED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('NUVAMA', 'global_risk_sentiment', -4::smallint, 'MODELLED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('NUVAMA', 'monsoon_index', 1::smallint, 'JUDGED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('NUVAMA', 'government_capex', 5::smallint, 'MEASURED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('NUVAMA', 'gst_collections_trend', 5::smallint, 'MEASURED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('NUVAMA', 'sector_regulatory_environment', 2::smallint, 'MODELLED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('MTNL', 'crude_oil', -3::smallint, 'MEASURED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('MTNL', 'dollar_rupee', -3::smallint, 'MODELLED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('MTNL', 'domestic_interest_rates', -2::smallint, 'JUDGED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('MTNL', 'global_risk_sentiment', -2::smallint, 'MODELLED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('MTNL', 'monsoon_index', 1::smallint, 'JUDGED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('MTNL', 'government_capex', -1::smallint, 'JUDGED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('MTNL', 'gst_collections_trend', 5::smallint, 'MEASURED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('MTNL', 'sector_regulatory_environment', 0::smallint, 'JUDGED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz)
) as v(ticker, factor_slug, sensitivity, mmj_tag, source_url, retrieved_at)
join public.instruments i on i.exchange = 'NSE' and i.ticker = v.ticker
join public.factors f on f.slug = v.factor_slug
on conflict (instrument_id, factor_id) do update set
  sensitivity = excluded.sensitivity,
  mmj_tag = excluded.mmj_tag,
  source_url = excluded.source_url,
  retrieved_at = excluded.retrieved_at;
