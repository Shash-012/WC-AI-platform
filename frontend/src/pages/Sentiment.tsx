import { Activity } from "@/components/icons";
import { ComingSoon } from "@/components/ComingSoon";

export function Sentiment() {
  return (
    <ComingSoon
      icon={Activity}
      eyebrow="Fan Sentiment"
      title="Sentiment"
      blurb="Live fan sentiment and buzz tracking across teams and players, coming soon."
      features={["Team buzz index", "Player mentions", "Momentum shifts"]}
    />
  );
}
