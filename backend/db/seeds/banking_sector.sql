-- P1-S5 seed: Banking sector + 8 macro factors per PRD §7.1 + ≥15 NSE banks × sensitivities.
-- Idempotent: safe to re-run after migration 0006_factor_db.sql.

insert into public.sectors (slug, name)
values ('banking', 'Banking & Financial Services')
on conflict (slug) do update set name = excluded.name;

insert into public.factors (slug, display_name, description, sort_order)
values 
  ('crude_oil', 'Crude oil price', 'India imports most crude — transmission to borrowers and collateral quality affects banks.', 1)
on conflict (slug) do update set
  display_name = excluded.display_name,
  description = excluded.description,
  sort_order = excluded.sort_order;

insert into public.factors (slug, display_name, description, sort_order)
values 
  ('dollar_rupee', 'Dollar–rupee rate', 'FX swings affect offshore borrowings and trade exposures of corporate loan books.', 2)
on conflict (slug) do update set
  display_name = excluded.display_name,
  description = excluded.description,
  sort_order = excluded.sort_order;

insert into public.factors (slug, display_name, description, sort_order)
values 
  ('domestic_interest_rates', 'Domestic interest rates', 'Repo-linked funding costs drive NIMs and provisioning cycles for lenders.', 3)
on conflict (slug) do update set
  display_name = excluded.display_name,
  description = excluded.description,
  sort_order = excluded.sort_order;

insert into public.factors (slug, display_name, description, sort_order)
values 
  ('global_risk_sentiment', 'Global risk sentiment', 'Risk-on/off drives FII participation in banking heavyweights and flow volatility.', 4)
on conflict (slug) do update set
  display_name = excluded.display_name,
  description = excluded.description,
  sort_order = excluded.sort_order;

insert into public.factors (slug, display_name, description, sort_order)
values 
  ('monsoon_index', 'Monsoon index', 'Rural disbursements and tractor/two-wheeler-linked asset quality in semi-urban books.', 5)
on conflict (slug) do update set
  display_name = excluded.display_name,
  description = excluded.description,
  sort_order = excluded.sort_order;

insert into public.factors (slug, display_name, description, sort_order)
values 
  ('government_capex', 'Government capex', 'Project finance pipelines linked to PSU/PPI and infrastructure disbursements.', 6)
on conflict (slug) do update set
  display_name = excluded.display_name,
  description = excluded.description,
  sort_order = excluded.sort_order;

insert into public.factors (slug, display_name, description, sort_order)
values 
  ('gst_collections_trend', 'GST collections trend', 'Consumption proxy informs retail credit cycle and SME book stress.', 7)
on conflict (slug) do update set
  display_name = excluded.display_name,
  description = excluded.description,
  sort_order = excluded.sort_order;

insert into public.factors (slug, display_name, description, sort_order)
values 
  ('sector_regulatory_environment', 'Sector regulatory environment', 'RBI norms, mergers, PCA, provisioning rules and SEBI banking disclosures.', 8)
on conflict (slug) do update set
  display_name = excluded.display_name,
  description = excluded.description,
  sort_order = excluded.sort_order;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'HDFCBANK', 'NSE', 'INE040A01034', 'HDFC Bank Ltd'
from public.sectors s where s.slug = 'banking'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'ICICIBANK', 'NSE', 'INE090A01021', 'ICICI Bank Ltd'
from public.sectors s where s.slug = 'banking'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'SBIN', 'NSE', 'INE062A01020', 'State Bank of India'
from public.sectors s where s.slug = 'banking'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'KOTAKBANK', 'NSE', 'INE237A01028', 'Kotak Mahindra Bank Ltd'
from public.sectors s where s.slug = 'banking'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'AXISBANK', 'NSE', 'INE238A01034', 'Axis Bank Ltd'
from public.sectors s where s.slug = 'banking'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'INDUSINDBK', 'NSE', 'INE095A01015', 'IndusInd Bank Ltd'
from public.sectors s where s.slug = 'banking'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'BANKBARODA', 'NSE', 'INE030A01018', 'Bank of Baroda'
from public.sectors s where s.slug = 'banking'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'PNB', 'NSE', 'INE016A01026', 'Punjab National Bank'
from public.sectors s where s.slug = 'banking'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'IDFCFIRSTB', 'NSE', 'INE092T01019', 'IDFC FIRST Bank Ltd'
from public.sectors s where s.slug = 'banking'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'FEDERALBNK', 'NSE', 'INE171A01029', 'The Federal Bank Ltd'
from public.sectors s where s.slug = 'banking'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'BANDHANBNK', 'NSE', 'INE545U01014', 'Bandhan Bank Ltd'
from public.sectors s where s.slug = 'banking'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'AUBANK', 'NSE', 'INE949L01017', 'AU Small Finance Bank Ltd'
from public.sectors s where s.slug = 'banking'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'YESBANK', 'NSE', 'INE528G01035', 'Yes Bank Ltd'
from public.sectors s where s.slug = 'banking'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'RBLBANK', 'NSE', 'INE976G01028', 'RBL Bank Ltd'
from public.sectors s where s.slug = 'banking'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instruments (sector_id, ticker, exchange, isin, display_name)
select s.id, 'UNIONBANK', 'NSE', 'INE695A01016', 'Union Bank of India'
from public.sectors s where s.slug = 'banking'
on conflict (exchange, ticker) do update set
  sector_id = excluded.sector_id,
  isin = excluded.isin,
  display_name = excluded.display_name;

insert into public.instrument_factor_sensitivity 
  (instrument_id, factor_id, sensitivity, mmj_tag, source_url, retrieved_at)
select
  i.id,
  f.id,
  v.sensitivity,
  v.mmj_tag,
  v.source_url,
  v.retrieved_at
from (values
  ('HDFCBANK', 'crude_oil', 3::smallint, 'JUDGED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('HDFCBANK', 'dollar_rupee', 0::smallint, 'MODELLED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('HDFCBANK', 'domestic_interest_rates', 2::smallint, 'MEASURED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('HDFCBANK', 'global_risk_sentiment', -4::smallint, 'JUDGED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('HDFCBANK', 'monsoon_index', 0::smallint, 'MODELLED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('HDFCBANK', 'government_capex', -4::smallint, 'MEASURED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('HDFCBANK', 'gst_collections_trend', 5::smallint, 'JUDGED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('HDFCBANK', 'sector_regulatory_environment', 3::smallint, 'MODELLED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('ICICIBANK', 'crude_oil', 4::smallint, 'MODELLED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('ICICIBANK', 'dollar_rupee', 2::smallint, 'MEASURED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('ICICIBANK', 'domestic_interest_rates', -2::smallint, 'JUDGED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('ICICIBANK', 'global_risk_sentiment', -2::smallint, 'MODELLED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('ICICIBANK', 'monsoon_index', -5::smallint, 'MEASURED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('ICICIBANK', 'government_capex', 2::smallint, 'JUDGED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('ICICIBANK', 'gst_collections_trend', 2::smallint, 'MODELLED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('ICICIBANK', 'sector_regulatory_environment', -2::smallint, 'MEASURED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('SBIN', 'crude_oil', 5::smallint, 'MEASURED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('SBIN', 'dollar_rupee', 2::smallint, 'JUDGED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('SBIN', 'domestic_interest_rates', 3::smallint, 'MODELLED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('SBIN', 'global_risk_sentiment', -2::smallint, 'MEASURED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('SBIN', 'monsoon_index', -3::smallint, 'JUDGED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('SBIN', 'government_capex', -5::smallint, 'MODELLED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('SBIN', 'gst_collections_trend', -2::smallint, 'MEASURED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('SBIN', 'sector_regulatory_environment', -2::smallint, 'JUDGED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('KOTAKBANK', 'crude_oil', -5::smallint, 'JUDGED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('KOTAKBANK', 'dollar_rupee', 4::smallint, 'MODELLED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('KOTAKBANK', 'domestic_interest_rates', -5::smallint, 'MEASURED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('KOTAKBANK', 'global_risk_sentiment', -4::smallint, 'JUDGED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('KOTAKBANK', 'monsoon_index', 4::smallint, 'MODELLED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('KOTAKBANK', 'government_capex', 1::smallint, 'MEASURED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('KOTAKBANK', 'gst_collections_trend', 1::smallint, 'JUDGED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('KOTAKBANK', 'sector_regulatory_environment', 5::smallint, 'MODELLED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('AXISBANK', 'crude_oil', 0::smallint, 'MODELLED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('AXISBANK', 'dollar_rupee', 3::smallint, 'MEASURED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('AXISBANK', 'domestic_interest_rates', 5::smallint, 'JUDGED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('AXISBANK', 'global_risk_sentiment', 5::smallint, 'MODELLED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('AXISBANK', 'monsoon_index', 5::smallint, 'MEASURED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('AXISBANK', 'government_capex', -5::smallint, 'JUDGED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('AXISBANK', 'gst_collections_trend', 2::smallint, 'MODELLED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('AXISBANK', 'sector_regulatory_environment', -2::smallint, 'MEASURED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('INDUSINDBK', 'crude_oil', 1::smallint, 'MEASURED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('INDUSINDBK', 'dollar_rupee', -1::smallint, 'JUDGED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('INDUSINDBK', 'domestic_interest_rates', -5::smallint, 'MODELLED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('INDUSINDBK', 'global_risk_sentiment', 5::smallint, 'MEASURED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('INDUSINDBK', 'monsoon_index', -4::smallint, 'JUDGED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('INDUSINDBK', 'government_capex', -4::smallint, 'MODELLED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('INDUSINDBK', 'gst_collections_trend', 0::smallint, 'MEASURED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('INDUSINDBK', 'sector_regulatory_environment', -3::smallint, 'JUDGED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('BANKBARODA', 'crude_oil', -4::smallint, 'JUDGED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('BANKBARODA', 'dollar_rupee', 5::smallint, 'MODELLED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('BANKBARODA', 'domestic_interest_rates', -4::smallint, 'MEASURED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('BANKBARODA', 'global_risk_sentiment', -2::smallint, 'JUDGED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('BANKBARODA', 'monsoon_index', 2::smallint, 'MODELLED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('BANKBARODA', 'government_capex', 0::smallint, 'MEASURED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('BANKBARODA', 'gst_collections_trend', 0::smallint, 'JUDGED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('BANKBARODA', 'sector_regulatory_environment', 3::smallint, 'MODELLED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('PNB', 'crude_oil', -4::smallint, 'MODELLED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('PNB', 'dollar_rupee', -4::smallint, 'MEASURED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('PNB', 'domestic_interest_rates', 0::smallint, 'JUDGED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('PNB', 'global_risk_sentiment', -3::smallint, 'MODELLED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('PNB', 'monsoon_index', 4::smallint, 'MEASURED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('PNB', 'government_capex', 4::smallint, 'JUDGED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('PNB', 'gst_collections_trend', 5::smallint, 'MODELLED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('PNB', 'sector_regulatory_environment', -5::smallint, 'MEASURED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('IDFCFIRSTB', 'crude_oil', 5::smallint, 'MEASURED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('IDFCFIRSTB', 'dollar_rupee', -1::smallint, 'JUDGED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('IDFCFIRSTB', 'domestic_interest_rates', 0::smallint, 'MODELLED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('IDFCFIRSTB', 'global_risk_sentiment', 1::smallint, 'MEASURED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('IDFCFIRSTB', 'monsoon_index', 0::smallint, 'JUDGED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('IDFCFIRSTB', 'government_capex', 2::smallint, 'MODELLED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('IDFCFIRSTB', 'gst_collections_trend', -1::smallint, 'MEASURED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('IDFCFIRSTB', 'sector_regulatory_environment', -2::smallint, 'JUDGED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('FEDERALBNK', 'crude_oil', -5::smallint, 'JUDGED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('FEDERALBNK', 'dollar_rupee', 5::smallint, 'MODELLED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('FEDERALBNK', 'domestic_interest_rates', -3::smallint, 'MEASURED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('FEDERALBNK', 'global_risk_sentiment', -1::smallint, 'JUDGED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('FEDERALBNK', 'monsoon_index', -5::smallint, 'MODELLED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('FEDERALBNK', 'government_capex', -5::smallint, 'MEASURED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('FEDERALBNK', 'gst_collections_trend', -5::smallint, 'JUDGED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('FEDERALBNK', 'sector_regulatory_environment', -1::smallint, 'MODELLED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('BANDHANBNK', 'crude_oil', 0::smallint, 'MODELLED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('BANDHANBNK', 'dollar_rupee', -4::smallint, 'MEASURED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('BANDHANBNK', 'domestic_interest_rates', 3::smallint, 'JUDGED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('BANDHANBNK', 'global_risk_sentiment', 1::smallint, 'MODELLED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('BANDHANBNK', 'monsoon_index', 1::smallint, 'MEASURED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('BANDHANBNK', 'government_capex', 2::smallint, 'JUDGED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('BANDHANBNK', 'gst_collections_trend', 5::smallint, 'MODELLED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('BANDHANBNK', 'sector_regulatory_environment', -1::smallint, 'MEASURED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('AUBANK', 'crude_oil', 0::smallint, 'MEASURED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('AUBANK', 'dollar_rupee', 2::smallint, 'JUDGED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('AUBANK', 'domestic_interest_rates', 2::smallint, 'MODELLED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('AUBANK', 'global_risk_sentiment', 0::smallint, 'MEASURED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('AUBANK', 'monsoon_index', -3::smallint, 'JUDGED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('AUBANK', 'government_capex', 0::smallint, 'MODELLED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('AUBANK', 'gst_collections_trend', 0::smallint, 'MEASURED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('AUBANK', 'sector_regulatory_environment', -1::smallint, 'JUDGED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('YESBANK', 'crude_oil', -5::smallint, 'JUDGED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('YESBANK', 'dollar_rupee', 5::smallint, 'MODELLED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('YESBANK', 'domestic_interest_rates', 3::smallint, 'MEASURED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('YESBANK', 'global_risk_sentiment', -5::smallint, 'JUDGED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('YESBANK', 'monsoon_index', 0::smallint, 'MODELLED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('YESBANK', 'government_capex', -5::smallint, 'MEASURED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('YESBANK', 'gst_collections_trend', -3::smallint, 'JUDGED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('YESBANK', 'sector_regulatory_environment', 1::smallint, 'MODELLED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('RBLBANK', 'crude_oil', -5::smallint, 'MODELLED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('RBLBANK', 'dollar_rupee', -2::smallint, 'MEASURED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('RBLBANK', 'domestic_interest_rates', -4::smallint, 'JUDGED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('RBLBANK', 'global_risk_sentiment', 2::smallint, 'MODELLED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('RBLBANK', 'monsoon_index', 0::smallint, 'MEASURED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('RBLBANK', 'government_capex', 3::smallint, 'JUDGED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('RBLBANK', 'gst_collections_trend', -2::smallint, 'MODELLED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('RBLBANK', 'sector_regulatory_environment', 4::smallint, 'MEASURED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz),
  ('UNIONBANK', 'crude_oil', -5::smallint, 'MEASURED'::public.mmj_type, 'https://pib.gov.in/Pressreleaseshare.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('UNIONBANK', 'dollar_rupee', 0::smallint, 'JUDGED'::public.mmj_type, 'https://www.rbi.org.in/scripts/ReferenceRateArchive.aspx', '2026-03-15T06:30:00+00'::timestamptz),
  ('UNIONBANK', 'domestic_interest_rates', 1::smallint, 'MODELLED'::public.mmj_type, 'https://website.rbi.org.in/web/monetary-policy/monetary-policy', '2026-03-15T06:30:00+00'::timestamptz),
  ('UNIONBANK', 'global_risk_sentiment', 0::smallint, 'MEASURED'::public.mmj_type, 'https://www.nseindia.com/resources/exchange-communication-guidelines-reports', '2026-03-15T06:30:00+00'::timestamptz),
  ('UNIONBANK', 'monsoon_index', -3::smallint, 'JUDGED'::public.mmj_type, 'https://mausam.imd.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('UNIONBANK', 'government_capex', -5::smallint, 'MODELLED'::public.mmj_type, 'https://www.indiabudget.gov.in/', '2026-03-15T06:30:00+00'::timestamptz),
  ('UNIONBANK', 'gst_collections_trend', -4::smallint, 'MEASURED'::public.mmj_type, 'https://www.cbic.gov.in/htdocs-cbec/gst/gst_documents', '2026-03-15T06:30:00+00'::timestamptz),
  ('UNIONBANK', 'sector_regulatory_environment', 2::smallint, 'JUDGED'::public.mmj_type, 'https://www.sebi.gov.in/legal/regulations.htm', '2026-03-15T06:30:00+00'::timestamptz)
) as v(ticker, factor_slug, sensitivity, mmj_tag, source_url, retrieved_at)
join public.instruments i
  on i.exchange = 'NSE' and i.ticker = v.ticker
join public.factors f
  on f.slug = v.factor_slug
on conflict (instrument_id, factor_id) do update set
  sensitivity = excluded.sensitivity,
  mmj_tag = excluded.mmj_tag,
  source_url = excluded.source_url,
  retrieved_at = excluded.retrieved_at;

