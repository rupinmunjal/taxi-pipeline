"use client";

import { BarChart, Card, Title } from "@tremor/react";

import { PanelSkeleton, PanelState } from "@/components/PanelState";
import type { RevenueByWeekday } from "@/lib/api";

interface Props {
  data: RevenueByWeekday[];
  loading: boolean;
  error: string | null;
}

export function RevenueByWeekdayChart({ data, loading, error }: Props) {
  return (
    <Card className="rounded-2xl border-zinc-200 shadow-sm">
      <Title>Average revenue by weekday</Title>
      <p className="mt-1 text-sm text-zinc-500">Average total trip charge in USD.</p>
      {loading ? <PanelSkeleton /> : null}
      {!loading && error ? <PanelState message={error} error /> : null}
      {!loading && !error && data.length === 0 ? <PanelState message="No revenue data for this range." /> : null}
      {!loading && !error && data.length > 0 ? (
        <BarChart
          className="taxi-revenue-chart mt-6 h-72"
          data={data}
          index="weekday"
          categories={["avg_revenue"]}
          colors={["amber"]}
          valueFormatter={(value) => `$${value.toFixed(2)}`}
          showLegend={false}
          yAxisWidth={56}
        />
      ) : null}
    </Card>
  );
}
