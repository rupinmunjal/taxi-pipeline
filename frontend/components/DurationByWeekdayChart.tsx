"use client";

import { Card, LineChart, Title } from "@tremor/react";

import { PanelSkeleton, PanelState } from "@/components/PanelState";
import type { DurationByWeekday } from "@/lib/api";

interface Props {
  data: DurationByWeekday[];
  loading: boolean;
  error: string | null;
}

export function DurationByWeekdayChart({ data, loading, error }: Props) {
  return (
    <Card className="rounded-2xl border-zinc-200 shadow-sm">
      <Title>Average duration by weekday</Title>
      <p className="mt-1 text-sm text-zinc-500">Average trip duration in minutes.</p>
      {loading ? <PanelSkeleton /> : null}
      {!loading && error ? <PanelState message={error} error /> : null}
      {!loading && !error && data.length === 0 ? <PanelState message="No duration data for this range." /> : null}
      {!loading && !error && data.length > 0 ? (
        <LineChart
          className="taxi-duration-chart mt-6 h-72"
          data={data}
          index="weekday"
          categories={["avg_trip_duration"]}
          colors={["amber"]}
          valueFormatter={(value) => `${value.toFixed(1)} min`}
          showLegend={false}
          yAxisWidth={62}
        />
      ) : null}
    </Card>
  );
}
