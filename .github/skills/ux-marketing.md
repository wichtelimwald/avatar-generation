---
name: UX & Marketing
description: >
  Apply when designing user experiences, writing copy, planning App Store
  presence, or creating marketing materials. Covers UX principles for iOS,
  App Store optimisation (ASO), onboarding flows, microcopy, and campaign
  content strategy.
---

# Skill: UX & Marketing

## Purpose

Defines UX and marketing standards for iOS app projects. Covers user
experience principles, App Store Optimisation, onboarding, microcopy,
and content strategy for campaigns.

---

## UX Principles for iOS

### The Three-Tap Rule
Any core action must be reachable within 3 taps from the home screen.
If it takes longer, reconsider the information architecture.

### Progressive Disclosure
Show only what the user needs *right now*. Reveal complexity on demand.
- First launch: show only the single most important action
- Advanced settings: buried under "..." or a settings screen
- Error detail: collapsed by default, expandable

### Thumb Zone (iPhone)
```
┌──────────────────────┐
│   ░░░░░░░░░░░░░░░░   │  ← Hard to reach (pinky zone)
│   ░░░░░░░░░░░░░░░░   │
│   ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒   │  ← Natural reach
│   ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒   │
│   ████████████████   │  ← Easy reach (thumb zone)
│   ████████████████   │
└──────────────────────┘
```
**Primary CTAs** → bottom 40% of screen
**Destructive actions** → top of screen (requires intentional reach)
**Tab bar** → always in thumb zone

### Empty States (Never Skip These)
Every list, feed, or data screen needs a designed empty state:
- **Icon**: relevant, not generic
- **Headline**: explain *why* it's empty (not "No items")
- **Body**: tell the user *what to do*
- **CTA button**: get them to the first value moment

---

## App Store Optimisation (ASO)

### Title (30 chars max)
```
[Brand Name] – [Primary Keyword]
Example: "FocusFlow – Deep Work Timer"
```
- Include your highest-volume keyword in the title
- Never use your brand name alone if it doesn't describe the app

### Subtitle (30 chars max)
Second-highest keyword cluster. Complement, don't repeat the title.
```
"Pomodoro, Focus & Productivity"
```

### Keywords Field (100 chars)
- No spaces after commas: `meditation,sleep,calm,breathe,anxiety`
- No words already in title/subtitle (wasted)
- Include misspellings of high-volume terms
- Refresh every 30–60 days based on performance

### Description Structure
```
[Hook – First 3 lines visible before "more"] ← Most important
────────────────────────────────────────────
Line 1: Core value proposition (what it does)
Line 2: Top differentiator (why yours)
Line 3: Social proof or stat ("500K users", "4.8 ★")

[Feature Bullets]
• Feature name — one line benefit
• Feature name — one line benefit

[Social Proof / Press]
"Best app of the year" – Publication Name

[CTA]
Download free. Premium from $X/month.
```

### Screenshots (Priority Order)
1. **Screenshot 1**: Biggest value prop headline + key screen
2. **Screenshot 2**: Core feature in action
3. **Screenshot 3**: Second key feature
4. **Screenshot 4–6**: Supporting features, social proof, awards
- Use captions on every screenshot (40–50 chars max)
- Always test light vs dark variant
- Localise screenshots for top 5 markets

### App Preview Video
- First 3 seconds must hook without sound (most users watch muted)
- Show the core "aha moment" within 6 seconds
- Length: 15–30 seconds optimal
- End on your best screen

---

## Onboarding Flow

### Principles
- **Time to value ≤ 60 seconds**: User must experience the core value before any paywall or sign-up
- **No mandatory sign-up on first launch**: Let users explore first
- **Permission requests**: Only ask at the moment of relevance, with clear rationale

### Permission Rationale Pattern
```swift
// Show a custom "pre-permission" screen BEFORE the system dialog
// System dialog has one chance – don't waste it

struct NotificationPermissionView: View {
    var body: some View {
        VStack {
            Image(systemName: "bell.badge")
            Text("Stay on track")
                .font(.title2.bold())
            Text("We'll remind you when it's time to focus – no noise, just nudges.")
                .multilineTextAlignment(.center)
            Button("Enable Notifications") { requestPermission() }
            Button("Not now") { dismiss() }
                .foregroundStyle(.secondary)
        }
    }
}
```

### Onboarding Screen Sequence
```
Welcome → Value Prop → [1–3 Key Features] → [Permission if needed]
→ Personalisation (max 2 questions) → First Core Action → Paywall (if applicable)
```

---

## Microcopy Standards

### Tone by Context
| Context | Tone | Example |
|---------|------|---------|
| Empty states | Encouraging, action-oriented | "Your favourites will live here. Start exploring →" |
| Errors | Apologetic, solution-focused | "Something went wrong. Check your connection and try again." |
| Success | Warm, celebratory | "All done! Your changes are saved." |
| Destructive action | Neutral, clear | "Delete task? This can't be undone." |
| Onboarding | Friendly, benefit-led | "Track your mood in under 10 seconds." |

### Button Copy Rules
```
❌ "OK", "Yes", "No", "Cancel" – generic, no meaning
✅ Describe the action: "Delete forever", "Save changes", "Start free trial"

❌ "Are you sure you want to delete this item?"
✅ "Delete 'Morning Routine'?" with buttons "Delete" / "Keep"
```

### Error Messages
```
Pattern: [What happened] + [Why] + [What to do]

❌ "Error 403"
❌ "Something went wrong."
✅ "Couldn't load your profile. Check your connection and pull to refresh."
✅ "Sign-in expired. Tap here to log in again."
```

---

## Content Marketing Framework

### App Launch Checklist
- [ ] App Store listing complete and localised (EN + top 3 markets)
- [ ] Press kit: icon, screenshots, app preview video, founder quote, key facts
- [ ] Landing page live with App Store badge
- [ ] Social accounts set up with consistent bio and link
- [ ] 3 teaser posts scheduled pre-launch
- [ ] Product Hunt listing prepared
- [ ] 10 review seeds identified (beta users, team, friends)

### Post-Launch Content Calendar (Week 1–4)
```
Week 1: Launch day post + story + response to every comment
Week 2: Feature spotlight (one key feature per day × 3)
Week 3: User story / testimonial (real screenshot with permission)
Week 4: Behind-the-scenes / how it was built
```

### Review Prompt Strategy
Ask for a review at peak happiness moments:
- After completing a task / achieving a milestone
- After 3+ sessions within 7 days
- After a successful share or export
- **Never**: on first launch, after an error, or more than twice in 90 days

```swift
// iOS 16+ native review prompt
import StoreKit

func requestReviewIfAppropriate() {
    guard sessionCount >= 3, daysSinceInstall >= 3 else { return }
    if let scene = UIApplication.shared.connectedScenes.first as? UIWindowScene {
        SKStoreReviewController.requestReview(in: scene)
    }
}
```
