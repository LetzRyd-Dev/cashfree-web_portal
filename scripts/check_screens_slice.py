with open("src/components/Screens.tsx", "r", encoding="utf-8") as f:
    text = f.read()

start_marker = "export const OperatorScreen: React.FC<OperatorScreenProps> = ({ fleet, onSelectVehicle, t }) => {"
end_marker = "/* =========================================================================\n   9. OPERATOR VEHICLE SCREEN"

idx1 = text.find(start_marker)
idx2 = text.find(end_marker)

print("Found markers:", idx1 != -1, idx2 != -1)
if idx1 != -1 and idx2 != -1:
    print("Length of OperatorScreen block:", idx2 - idx1)
