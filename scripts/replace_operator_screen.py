new_operator_screen = """export const OperatorScreen: React.FC<OperatorScreenProps> = ({ fleet, onSelectVehicle, t }) => {
  const [searchQuery, setSearchQuery] = useState('');

  const totalVehicles = fleet.vehicles.length;
  const totalToPay = fleet.vehicles.reduce((sum, v) => (v.currentWeekOs < 0 ? sum + Math.abs(v.currentWeekOs) : sum), 0);
  const totalToCollect = fleet.vehicles.reduce((sum, v) => (v.currentWeekOs > 0 ? sum + v.currentWeekOs : sum), 0);

  const vehicleFleetList = fleet.vehicles.filter(
    (v) =>
      v.number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.model.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.make.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.driverName.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const formatCurrency = (val: number) => {
    const hasDecimals = val % 1 !== 0;
    return '₹' + Math.abs(val).toLocaleString('en-IN', {
      minimumFractionDigits: hasDecimals ? 2 : 0,
      maximumFractionDigits: 2,
    });
  };

  return (
    <div className="space-y-4 text-left font-sans">
      <div>
        <h2 className="font-sans text-base font-bold text-text">
          {t('operator.dashboardTitle', 'Fleet Overview')}
        </h2>
        <p className="font-sans text-xs text-text-muted mt-0.5">
          {t('operator.statusSubtitle', 'Real-time settlement status')} ({totalVehicles} {t('operator.vehiclesUnit', 'Vehicles')})
        </p>
      </div>

      <div className="grid grid-cols-3 gap-2 font-sans text-xs">
        <div className="p-2.5 sm:p-3 bg-surface border border-border rounded-xl text-center shadow-xs flex flex-col justify-between">
          <p className="text-[10px] font-bold text-text-muted uppercase tracking-wider">{t('operator.toPay', 'TO PAY')}</p>
          <p className="font-sans text-xs sm:text-sm font-bold text-green mt-1 whitespace-nowrap font-mono">
            +{formatCurrency(totalToPay)}
          </p>
        </div>
        <div className="p-2.5 sm:p-3 bg-surface border border-border rounded-xl text-center shadow-xs flex flex-col justify-between">
          <p className="text-[10px] font-bold text-text-muted uppercase tracking-wider">{t('operator.toCollect', 'TO COLLECT')}</p>
          <p className="font-sans text-xs sm:text-sm font-bold text-red-600 mt-1 whitespace-nowrap font-mono">
            -{formatCurrency(totalToCollect)}
          </p>
        </div>
        <div className="p-2.5 sm:p-3 bg-surface border border-border rounded-xl text-center shadow-xs flex flex-col justify-between">
          <p className="text-[10px] font-bold text-text-muted uppercase tracking-wider">{t('operator.cars', 'CARS')}</p>
          <p className="font-sans text-xs sm:text-sm font-bold text-text mt-1">{totalVehicles}</p>
        </div>
      </div>

      {/* Fleet Security Deposit Card */}
      <div className="bg-surface border border-border rounded-xl p-3 shadow-xs text-left font-sans text-xs">
        <div className="flex items-center justify-between">
          <span className="font-sans text-xs font-bold text-text uppercase tracking-wider">
            {t('operator.fleetDeposit', 'FLEET SECURITY DEPOSIT')}
          </span>
          <div className="flex items-center gap-3 text-xs font-sans">
            <span>
              <span className="text-text-muted font-medium">{t('hisaab.paid', 'Paid:')} </span>
              <span className="font-bold text-green">
                ₹{(fleet.depositPaidSoFar || 20000).toLocaleString('en-IN', { minimumFractionDigits: (fleet.depositPaidSoFar || 20000) % 1 !== 0 ? 2 : 0, maximumFractionDigits: 2 })}
              </span>
            </span>
            <span>
              <span className="text-text-muted font-medium">{t('hisaab.pending', 'Pending:')} </span>
              <span className="font-bold text-amber-700">
                ₹{(fleet.depositPending ?? 0).toLocaleString('en-IN', { minimumFractionDigits: (fleet.depositPending ?? 0) % 1 !== 0 ? 2 : 0, maximumFractionDigits: 2 })}
              </span>
            </span>
          </div>
        </div>
      </div>

      {/* SEARCH BAR */}
      <div className="relative">
        <Search className="w-4 h-4 text-text-muted absolute left-3 top-3" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder={t('operator.searchVehiclePlaceholder', 'Search vehicle number, model or driver...')}
          className="w-full pl-9 pr-3 py-2 rounded-xl border border-border bg-bg text-xs font-medium outline-none focus:border-primary transition-colors"
        />
      </div>

      {/* VEHICLE FLEET LIST CARD */}
      <div className="bg-surface border border-border rounded-xl p-3.5 shadow-sm space-y-2.5">
        <div className="border-b border-border/60 pb-2 flex items-center justify-between">
          <h3 className="font-sans text-xs font-bold text-text uppercase tracking-wider flex items-center gap-1.5">
            <Car className="w-3.5 h-3.5 text-primary" />
            <span>{t('operator.vehicleFleet', 'VEHICLE FLEET')} ({vehicleFleetList.length})</span>
          </h3>
          <span className="text-[10px] font-semibold text-text-muted">{t('operator.tapToView', 'Tap to view Hisaab')}</span>
        </div>

        <div className="divide-y divide-border/60">
          {vehicleFleetList.length === 0 ? (
            <div className="py-6 text-center text-text-muted text-xs">
              {searchQuery ? t('operator.noVehiclesMatch', 'No vehicles match your search') : t('operator.noVehicles', 'No vehicles assigned to this fleet')}
            </div>
          ) : (
            vehicleFleetList.map((v) => (
              <div
                key={`v-${v.number}`}
                onClick={() => onSelectVehicle(v.number)}
                className="py-2.5 flex items-center justify-between first:pt-0 last:pb-0 hover:bg-bg/60 cursor-pointer rounded-md px-1 transition-colors group"
              >
                <div className="flex items-center gap-2.5 min-w-0 flex-1 pr-2">
                  <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border bg-emerald-500/10 border-emerald-500/20 text-emerald-600">
                    <Car className="w-4 h-4" />
                  </div>

                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-1.5">
                      <span className="font-mono text-xs font-black text-text tracking-wide bg-bg px-1.5 py-0.5 rounded border border-border/60">
                        {v.number}
                      </span>
                      <span className="text-[10px] font-semibold text-text-muted font-sans truncate">
                        {v.make} {v.model}
                      </span>
                    </div>
                    <p className="font-sans text-[11px] text-text-muted mt-1 flex items-center gap-1 truncate">
                      <span className="text-[10px] uppercase font-bold text-text-muted/80">Assigned Driver:</span>
                      <span className="font-semibold text-text truncate">{v.driverName || 'Unassigned'}</span>
                    </p>
                  </div>
                </div>

                <div className="text-right shrink-0 flex flex-col items-end">
                  {v.currentWeekOs < 0 ? (
                    <span className="font-sans text-xs font-bold text-green whitespace-nowrap font-mono">
                      +{formatCurrency(v.currentWeekOs)}
                    </span>
                  ) : v.currentWeekOs > 0 ? (
                    <span className="font-sans text-xs font-bold text-red-600 whitespace-nowrap font-mono">
                      -{formatCurrency(v.currentWeekOs)}
                    </span>
                  ) : (
                    <span className="font-sans text-xs font-bold text-text-muted font-mono">
                      ₹0
                    </span>
                  )}
                  <span className="font-sans text-[10px] font-bold text-primary group-hover:underline mt-0.5 whitespace-nowrap">
                    View Hisaab →
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
"""

with open("src/components/Screens.tsx", "r", encoding="utf-8") as f:
    text = f.read()

start_marker = "export const OperatorScreen: React.FC<OperatorScreenProps> = ({ fleet, onSelectVehicle, t }) => {"
end_marker = "/* =========================================================================\n   9. OPERATOR VEHICLE SCREEN"

idx1 = text.find(start_marker)
idx2 = text.find(end_marker)

if idx1 != -1 and idx2 != -1:
    new_text = text[:idx1] + new_operator_screen.strip() + "\n\n" + text[idx2:]
    with open("src/components/Screens.tsx", "w", encoding="utf-8") as f:
        f.write(new_text)
    print("Successfully replaced OperatorScreen with vehicle-centric layout!")
else:
    print("Could not find markers!")
