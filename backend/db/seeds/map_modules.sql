-- P2-S11 seed: Map modules per sector + reasoning-gap cross-links (P2-S4 taxonomy).

-- Reasoning-gap modules (sector_slug null — apply across sectors)
insert into public.map_modules (id, sector_slug, title, body, linked_gap_types, sort_order)
values
  (
    'a1000001-0001-4000-8000-000000000001'::uuid,
    null,
    'Direction vs magnitude',
    'When your mechanism read is right but the market move undershoots or overshoots, check whether you sized the second-order effect (liquidity, positioning, index weight) rather than re-litigating the headline narrative.',
    array['direction_magnitude_mismatch']::text[],
    1
  ),
  (
    'a1000001-0001-4000-8000-000000000002'::uuid,
    null,
    'Narrative vs mechanism',
    'Strong stories can mask weak transmission chains. Before logging a prediction, write one sentence on *how* the event reaches earnings or flows — then compare that chain to the Factor DB sensitivities for your ticker.',
    array['narrative_anchoring']::text[],
    2
  ),
  (
    'a1000001-0001-4000-8000-000000000003'::uuid,
    null,
    'Sector concentration',
    'If most of your resolved predictions cluster in one sector, your accuracy stats may reflect sector beta more than reasoning skill. Use The Map to rotate through a second sector with different factor loadings before your next batch of cards.',
    array['sector_concentration']::text[],
    3
  )
on conflict (id) do update set
  sector_slug = excluded.sector_slug,
  title = excluded.title,
  body = excluded.body,
  linked_gap_types = excluded.linked_gap_types,
  sort_order = excluded.sort_order;

-- Per-sector "How this sector reacts to events" modules
insert into public.map_modules (id, sector_slug, title, body, linked_gap_types, sort_order)
values
  (
    'b2000001-0001-4000-8000-000000000001'::uuid,
    'banking',
    'How Banking reacts to events',
    'Rate-cycle and regulatory headlines move NIM and provisioning expectations first; crude and FX pass through corporate borrowers and trading books. FII risk-off often hits large private banks before PSU names because of liquidity and index weight.',
    '{}'::text[],
    10
  ),
  (
    'b2000001-0001-4000-8000-000000000002'::uuid,
    'it',
    'How IT reacts to events',
    'USD revenue and client discretionary spend dominate; a stronger rupee compresses reported growth while global risk-off hits deal pipelines. Domestic rate moves matter less than US tech capex and visa or immigration policy headlines.',
    '{}'::text[],
    10
  ),
  (
    'b2000001-0001-4000-8000-000000000003'::uuid,
    'energy',
    'How Energy & Oil reacts to events',
    'Crude and gas prices transmit quickly to refining margins and E&P cash flows; government fuel pricing and subsidy politics add a domestic overlay. Renewables and grid names react to policy and tender headlines more than spot crude alone.',
    '{}'::text[],
    10
  ),
  (
    'b2000001-0001-4000-8000-000000000004'::uuid,
    'fmcg',
    'How FMCG reacts to events',
    'Volume growth tracks rural demand and GST or tax pass-through; input inflation (crude-linked packaging, agri) hits margins with a lag. Defensive positioning means global risk-off is usually mild unless FX moves sharply on imported inputs.',
    '{}'::text[],
    10
  ),
  (
    'b2000001-0001-4000-8000-000000000005'::uuid,
    'auto',
    'How Auto reacts to events',
    'Fuel prices, rates, and monsoon drive near-term demand; commodity costs (steel, aluminium) hit margins. Export-heavy and EV names add FX and subsidy/regulatory sensitivity on top of the domestic cycle.',
    '{}'::text[],
    10
  ),
  (
    'b2000001-0001-4000-8000-000000000006'::uuid,
    'pharma',
    'How Pharma reacts to events',
    'US FDA and pricing headlines move exporters; domestic policy on essential medicines and GST affects India formulations. FX helps exporters on a weaker rupee; regulatory quality issues are idiosyncratic but sector-wide when trust breaks.',
    '{}'::text[],
    10
  ),
  (
    'b2000001-0001-4000-8000-000000000007'::uuid,
    'metals',
    'How Metals reacts to events',
    'China demand and global industrial sentiment set the base; domestic infra and capex support domestic steel and aluminium. Crude and freight affect costs; government mining or duty policy can re-rate the whole chain in one session.',
    '{}'::text[],
    10
  ),
  (
    'b2000001-0001-4000-8000-000000000008'::uuid,
    'telecom',
    'How Telecom reacts to events',
    'ARPU and spectrum policy drive domestic operators; tower cos lever to traffic growth. FX matters for equipment imports; regulatory fines or tariff orders can dominate a quarter narrative faster than macro factors.',
    '{}'::text[],
    10
  ),
  (
    'b2000001-0001-4000-8000-000000000009'::uuid,
    'infra',
    'How Infra & Capital Goods reacts to events',
    'Order inflows track government capex, state budgets, and RBI rates via project finance costs. Cement and real estate within the cluster react to housing policy; execution and working-capital headlines are stock-specific but sector-correlated.',
    '{}'::text[],
    10
  )
on conflict (id) do update set
  sector_slug = excluded.sector_slug,
  title = excluded.title,
  body = excluded.body,
  linked_gap_types = excluded.linked_gap_types,
  sort_order = excluded.sort_order;
