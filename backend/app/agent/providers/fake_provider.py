import asyncio
import re
from typing import AsyncIterator, Dict, List, Optional
from app.agent.providers.llm_provider import LLMProvider
from app.agent.prompts import STANDARD_REFUSAL_MESSAGE


class FakeLLMProvider(LLMProvider):
    """
    Deterministic mock LLM provider for unit and integration testing.
    Produces grounded mock answers, full ~1,250-word Ship 30 essays, or explicit refusals.
    """

    def __init__(
        self,
        custom_response: Optional[str] = None,
        should_raise: Optional[Exception] = None,
        is_healthy: bool = True,
        model: str = "mock-lenny-v1",
    ):
        self.custom_response = custom_response
        self.should_raise = should_raise
        self.is_healthy = is_healthy
        self.model = model
        self.last_prompt: Optional[str] = None
        self.last_system_prompt: Optional[str] = None
        self.last_turn_history: Optional[List[Dict[str, str]]] = None

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        turn_history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        full_text = await self.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        words = full_text.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
            await asyncio.sleep(0.001)

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        turn_history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        self.last_prompt = prompt
        self.last_system_prompt = system_prompt
        self.last_turn_history = turn_history

        if self.should_raise:
            raise self.should_raise

        if self.custom_response:
            return self.custom_response

        # Check if evidence is missing
        if "NO RELEVANT TRANSCRIPT EVIDENCE FOUND" in prompt:
            return STANDARD_REFUSAL_MESSAGE

        # Extract guest names and episodes from prompt evidence excerpts
        guests = re.findall(r"Guest:\s*(.+)", prompt)
        episodes = re.findall(r"Episode:\s*(.+)", prompt)

        guest_str = guests[0] if guests else "the guest speaker"
        episode_str = episodes[0].split("|")[0].strip() if episodes else "Lenny's Podcast"

        # Check if this is a Ship 30 essay generation request
        is_ship30 = (
            (system_prompt and "Ship 30 for 30" in system_prompt)
            or "[EDITORIAL CUSTOMIZATION GUIDELINES]" in prompt
            or "Ship 30" in prompt
            or "ship30" in prompt
        )

        if is_ship30:
            return self._generate_mock_ship30_essay(guest_str, episode_str, prompt)

        # Contextual multi-turn follow-up synthesis if previous turns exist
        if turn_history and len(turn_history) > 0:
            last_user_turn = next((t["content"] for t in reversed(turn_history) if t.get("role") == "user"), "")
            return (
                f"Building on our previous discussion regarding {guest_str}'s insights in '{episode_str}', "
                f"here is how that applies specifically:\n\n"
                f"1. **Contextual Application**: {guest_str} highlights that applying this framework requires adapting metrics to your specific product stage.\n"
                f"2. **Operational Leverage**: Focus on the core inflection point identified earlier to avoid unnecessary team thrash.\n"
                f"3. **Execution Guardrail**: Maintain continuous qualitative customer touchpoints alongside quantitative cohort data."
            )

        # Standard Q&A response
        return (
            f"Based on Lenny's Podcast with {guest_str} ('{episode_str}'), "
            f"here are the core principles:\n\n"
            f"1. **Core Framework**: {guest_str} explains that successful execution requires focusing on high-leverage loops and qualitative feedback.\n"
            f"2. **Key Metric & Retention**: Aligning activation metrics with user value is critical for sustainable growth.\n"
            f"3. **Practical Application**: Teams should prioritize continuous experimentation and structured customer discovery."
        )

    def _generate_mock_ship30_essay(self, guest: str, episode: str, prompt: str) -> str:
        """
        Generate a comprehensive, skimmable ~1,250-word editorial essay
        with hook, narrative tension, 3 grounded pillars, practical implementation, and takeaway checklist.
        """
        return f"""# The Growth Engine Paradox: Why Traditional Product Playbooks Fail

Most product teams are running as fast as they can in the wrong direction.

They pour millions into top-of-funnel acquisition, celebrate record sign-up spikes on launch day, and convince themselves that growth is merely a marketing arithmetic problem. 

Then reality hits. Ninety days later, the cohort retention curve resembles a ski slope, active users drop off a cliff, and the team scrambles to buy more paid traffic to plug the leaking bucket.

This is the central tension of modern technology building: **Acquisition is loud, but retention is quiet. And in the long run, retention is the only metric that matters.**

In a standout discussion on Lenny's Podcast with {guest} on *{episode}*, a counterintuitive truth emerges that dismantles conventional SaaS wisdom. True enterprise value isn't built on brute-force funnels; it is engineered through compounding, self-reinforcing loops and obsessive focus on user value realization.

Here is the strategic blueprint for how elite product and growth leaders rethink their growth engine from first principles.

---

## The Core Tension: Funnels vs. Compounding Loops

For two decades, product managers were taught the classic pirate funnel: Acquisition, Activation, Retention, Referral, Revenue (AARRR).

The flaw in the funnel model is structural: it treats users as linear inputs that flow down a pipe and fall out the bottom. Every single quarter, the team must replenish the top of the funnel with fresh capital, fresh ads, and fresh outbound sales. When marketing spend stops, the business stops growing.

As {guest} articulates in *{episode}*, high-growth market leaders do not operate linear funnels. They build closed-loop systems where the output of one cohort of users becomes the input for the next cohort.

When a user interacts with your core product loop:
* They generate new content or data that attracts new visitors (content loops).
* They invite colleagues or collaborate across team boundaries (viral product loops).
* Or they pay for expanding software licenses, funding continuous R&D and organic brand distribution (paid reinvestment loops).

The difference between a linear funnel and a compounding loop is the difference between simple addition and exponential growth.

---

## Pillar 1: Finding the Signal in the Noise (Quantitative PMF)

Before you can accelerate a growth loop, you must prove that the product delivers undeniable, irreplaceable value.

Too many teams confuse early customer curiosity with genuine Product-Market Fit. In *{episode}*, {guest} highlights why relying on vanity metrics like registered accounts or page views is lethal for early-stage companies.

Instead of tracking aggregate signups, elite founders track leading indicators of user desperation:
1. **The 40% Rule**: If at least 40% of surveyed active users state they would be "very disappointed" if your product disappeared tomorrow, you have a defensible core engine.
2. **Segment Isolation**: If the overall score is below the threshold, isolate the passionate power users who answered "very disappointed" and ruthlessly ignore the rest when defining your core roadmap.
3. **Double Down on Strengths**: Spend 50% of engineering bandwidth deepening what your best customers love, and the other 50% removing specific friction points holding back high-intent prospects.

When you treat PMF as an objective metric rather than an emotional intuition, product priorities become crystal clear.

---

## Pillar 2: The Self-Serve Flywheel and the New B2B Reality

The era of heavy, gated enterprise sales as the sole entry point for software is over.

In today's landscape, end users expect immediate gratification. As {guest} emphasizes in *{episode}*, the modern product experience must deliver value before asking for enterprise procurement approval.

This shift transforms the traditional sales cycle into a continuous user adoption loop:
* **Frictionless Onboarding**: Strip away mandatory onboarding calls, complex setup wizards, and invasive form fields. The time-to-first-value (TTFV) should be measured in seconds, not weeks.
* **Product-Qualified Leads (PQLs)**: Instead of scoring leads by company size or job title, score accounts based on active product usage milestones (e.g., inviting 3 teammates, running 10 queries, or embedding a dashboard).
* **Expansion Flywheels**: When an enterprise sales representative eventually reaches out to leadership, the deal is already 80% won because 50 engineers inside the organization are already using the tool every day.

By designing software that employees love using, you turn end users into your most effective sales team.

---

## Pillar 3: High-Leverage Execution and Operational Velocity

Having a compelling strategy is worthless without the operational discipline to execute with high tempo and rigor.

In *{episode}*, {guest} breaks down how top product organizations structure their daily workflow to prevent analysis paralysis:
* **Categorize Tasks by Leverage**: Differentiate between High-Leverage work (setting core product architecture and defining strategic flywheels), Neutral work (standard roadmap delivery), and Overhead work (unnecessary meetings and repetitive status reporting).
* **Run Controlled Experimentation Sprints**: Establish clear hypotheses with binary success criteria. Every growth experiment should have a defined owner, a target metric uplift, and a predetermined kill-date if it fails to show statistical significance.
* **Normalize Rapid Pruning**: Winning teams celebrate killing underperforming features as much as shipping new ones. Product bloat is the enemy of retention.

Velocity is not about working 80 hours a week; it is about eliminating low-leverage distractions so your highest-conviction bets get 100% of your energy.

---

## Practical Implementation: How to Apply This Tomorrow

Transforming an organization from a linear funnel mindset to a grounded growth engine requires systematic changes in operating cadence.

Here is how high-performing product teams operationalize these principles:

### 1. Audit Your Existing Growth Mechanics
Map every user journey on a single whiteboard. Identify whether each acquisition channel feeds a self-sustaining loop or whether it requires constant manual reinvestment. If a channel cannot compound, categorize it as a temporary booster rather than a core growth pillar.

### 2. Establish a Single North Star Activation Metric
Stop tracking 20 disparate KPIs across four dashboards. Pick the single user action that correlates most strongly with long-term 90-day retention. Align design, engineering, and product around maximizing the percentage of new users who complete that milestone within their first 7 days.

### 3. Build a Cross-Functional Growth Pod
Break down the silos between product managers, data analysts, and growth engineers. Give the dedicated growth pod full autonomy to experiment on the onboarding flow, activation triggers, and viral sharing mechanics without waiting for monthly executive review cycles.

---

## Try This Next: The 5-Step Execution Blueprint

If you want to put the insights from {guest} into action immediately, execute this 5-step sprint:

1. **Survey Your Active Cohort**: Send a 3-question survey asking: *"How would you feel if you could no longer use our product?"* Segment the responses immediately.
2. **Interview the High-Disappointment Group**: Schedule 10 conversations with users who cannot live without your product. Uncover their exact workflow, their primary alternative, and the specific moment they realized your tool was indispensable.
3. **Map the Critical Path**: Document every click and form field between registration and the core value moment. Eliminate at least 30% of the friction points in the next release.
4. **Define Your Primary Loop**: Choose one primary growth loop (Content, Viral Collaboration, or Paid Expansion) and commit all new growth resources to perfecting that specific engine.
5. **Set a Weekly Review Cadence**: Track your North Star metric weekly with your core team. Review experiment velocity, celebrate validated learnings, and ruthlessly deprecate stalled initiatives.

---

## Final Thoughts: The Compounding Advantage

Great companies are rarely built on a single silver-bullet feature or a viral PR stunt.

They are built by teams that understand the physics of growth: that sustainable momentum is the product of hundreds of disciplined, grounded decisions compounded over time.

As {guest} demonstrated throughout *{episode}*, when you align your product experience with genuine customer value, stop pushing linear funnels, and build self-reinforcing loops, growth ceases to be an uphill battle. It becomes inevitable.
"""

    async def check_health(self) -> bool:
        return self.is_healthy
