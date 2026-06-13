import { LineChart } from "@/components/icons";
import { ComingSoon } from "@/components/ComingSoon";

export function Predictor() {
  return (
    <ComingSoon
      icon={LineChart}
      eyebrow="Match Predictor"
      title="Predictor"
      blurb="Model-driven win probabilities and group-stage simulations are on the way."
      features={["Win probability", "Group simulations", "Form-weighted models"]}
    />
  );
}
