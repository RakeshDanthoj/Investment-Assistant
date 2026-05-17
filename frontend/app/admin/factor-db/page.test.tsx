import { render, screen } from "@testing-library/react";

import FactorMatrix from "./_components/FactorMatrix";

describe("FactorMatrix", () => {
  it("renders instrument rows and factor cells with MMJ label", () => {
    render(
      <FactorMatrix
        sectorName="Banking & Financial Services"
        factors={[
          { slug: "crude_oil", display_name: "Crude oil price", sort_order: 1 },
          { slug: "dollar_rupee", display_name: "Dollar–rupee rate", sort_order: 2 },
        ]}
        instruments={[
          {
            id: "1",
            ticker: "SBIN",
            display_name: "State Bank of India",
            isin: "INE062A01020",
            exchange: "NSE",
          },
        ]}
        sensitivities={{
          SBIN: {
            crude_oil: {
              sensitivity: -2,
              mmj_tag: "JUDGED",
              source_url: "https://example.com",
              retrieved_at: "2026-03-15T06:30:00Z",
              freshness: "green",
            },
          },
        }}
      />,
    );

    expect(screen.getByText("State Bank of India")).toBeInTheDocument();
    expect(screen.getByText(/SBIN\s*·/)).toBeInTheDocument();
    expect(screen.getByText("-2")).toBeInTheDocument();
    expect(screen.getByText("JUDGED")).toBeInTheDocument();
  });
});
