"use client";

import {
  Card,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
  Title,
} from "@tremor/react";

import { PanelSkeleton, PanelState } from "@/components/PanelState";
import type { TopZone } from "@/lib/api";

interface Props {
  data: TopZone[];
  loading: boolean;
  error: string | null;
}

const currency = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

export function TopZonesTable({ data, loading, error }: Props) {
  return (
    <Card className="rounded-2xl border-zinc-200 shadow-sm">
      <Title>Top pickup zones</Title>
      <p className="mt-1 text-sm text-zinc-500">Ten pickup location IDs with the highest total revenue.</p>
      {loading ? <PanelSkeleton /> : null}
      {!loading && error ? <PanelState message={error} error /> : null}
      {!loading && !error && data.length === 0 ? <PanelState message="No pickup-zone data for this range." /> : null}
      {!loading && !error && data.length > 0 ? (
        <Table className="mt-6">
          <TableHead>
            <TableRow>
              <TableHeaderCell>Rank</TableHeaderCell>
              <TableHeaderCell>Pickup zone ID</TableHeaderCell>
              <TableHeaderCell className="text-right">Revenue</TableHeaderCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data.map((zone, index) => (
              <TableRow key={zone.zone_id}>
                <TableCell className="font-mono text-zinc-500">{String(index + 1).padStart(2, "0")}</TableCell>
                <TableCell className="font-medium text-zinc-900">Zone {zone.zone_id}</TableCell>
                <TableCell className="text-right font-mono font-medium text-zinc-900">
                  {currency.format(zone.revenue)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      ) : null}
    </Card>
  );
}
