import { StateBadge } from "@/components/common/StatusBadge";
import { formatMoney } from "@/lib/workbench/format";
import type { ClientCase } from "@/lib/workbench/types";

export function StressTest({
  stressTest,
  selectedScenarioId,
  onSelect,
}: {
  stressTest: NonNullable<ClientCase["collateralStressTest"]> | undefined;
  selectedScenarioId: string | null;
  onSelect: (id: string) => void;
}) {
  if (!stressTest) return <div className="surface-content"><p className="muted">No bounded Collateral Stress Test was supplied for this Client Case.</p></div>;
  const selected = stressTest.scenarios.find((scenario) => scenario.id === selectedScenarioId) ?? stressTest.scenarios[0];
  if (!selected) return <div className="surface-content"><p className="muted">No scenarios were supplied.</p></div>;
  return (
    <div className="surface-content stress-test">
      <div className="guardrail-banner">{stressTest.label}</div>
      <label className="select-field">Supplied scenario
        <select value={selected.id} onChange={(event) => onSelect(event.target.value)}>
          {stressTest.scenarios.map((scenario) => <option key={scenario.id} value={scenario.id}>{scenario.collateralChangePct === 0 ? "Base" : `${scenario.collateralChangePct}% collateral`} · {scenario.status}</option>)}
        </select>
      </label>
      <div className="scenario-hero">
        <span>Calculated LTV</span><strong>{selected.ltvPct.toFixed(2)}%</strong><StateBadge value={selected.status} />
      </div>
      <dl className="scenario-values">
        <div><dt>Collateral assumption</dt><dd>{selected.collateralChangePct.toFixed(0)}%</dd></div>
        <div><dt>Collateral market value</dt><dd>{formatMoney(selected.collateralValue)}</dd></div>
        <div><dt>Lending value</dt><dd>{formatMoney(selected.lendingValue)}</dd></div>
        <div><dt>Drawn amount · unchanged</dt><dd>{formatMoney(selected.drawnAmount)}</dd></div>
        <div><dt>Facility trigger</dt><dd>{selected.triggerPct.toFixed(2)}%</dd></div>
        <div><dt>Distance to trigger</dt><dd>{selected.distanceToTriggerPctPoints.toFixed(2)} percentage points</dd></div>
      </dl>
      <p className="boundary-note">The deterministic engine supplied every value shown. The browser does not recalculate LTV or assign scenario probability, and this is not a trade recommendation.</p>
    </div>
  );
}
