# How to present this deck

For each slide: what to say, the one point that must land, and the question you are most likely to get.

**Total time: about 12 minutes.** Roughly a minute a slide, two on the chart.

---

## Before you start

**The single message of this whole presentation:**

> "I have not built anything yet. I have understood the data — including what it cannot do."

Everything else supports that. If they remember one thing, it should be that you looked properly before you started building.

**Three habits that will carry the whole talk:**

1. **Do not read the slides.** They can read. Say the thing behind the words.
2. **When you do not know, say so and say how you would find out.** "I do not know yet — I would check X" is a strong answer. Guessing is the only wrong answer.
3. **Slow down on slides 4, 8 and 11.** Those are the three that make an impression.

**Opening line:**

> "Before I build anything, I wanted to understand what the bank has actually given me. This is what I found — including a few things I got wrong."

That last clause buys you enormous goodwill. It tells them you are going to be honest, so everything after it is more believable.

---

## Slide 1 — Where I am in the project

**Say:** "This is the first stage. I have opened the file, looked at what is in it, and drawn some pictures. I have not analysed anything properly yet and I have not built a model. I want to be clear about that because everything I say today is about understanding, not results."

**The point to land:** you are setting expectations honestly. Nobody can accuse you of overselling.

**Understand:** the file has six months of behaviour per customer, plus who they are and what they hold, plus whether they left. That last column is what makes learning possible at all — without it there is nothing to learn from.

**If asked "why haven't you built a model yet?"** — "Because a model built on data I do not understand would be worse than useless, it would be confidently wrong. Two of the things I found this week would have quietly ruined it."

---

## Slide 2 — The question I had to ask before anything else

**Say:** "The very first thing I needed was something the file could not tell me: whether month one is the oldest month or the newest. I asked rather than assumed."

**The point to land:** you asked instead of guessing, on something that looked trivial and wasn't.

**Understand:** everything you build measures direction. If the order were reversed, a customer whose spending was collapsing would look like one whose spending was growing. The model would have learned the exact opposite of the truth *and still appeared to work*, because it would be consistently wrong in a consistent way.

**If asked "how would you have caught it?"** — be honest: "I might not have, and that is the point. It would not have crashed or thrown an error. That is why I asked."

---

## Slide 3 — The six months of spending

**Say:** "Looking at any single month, customers who left and customers who stayed spend about the same. If I had stopped there I would have thrown those columns away."

**The point to land:** the obvious first look gave the wrong answer.

**Understand:** this is the setup for the next two slides. You are building tension — the columns look useless, and they turn out to be the most valuable thing in the file.

**If asked "so why did you keep looking?"** — "Because six columns of behaviour over time is the only thing in the file that shows change. Everything else is a fixed fact about the person. It seemed worth more than one glance."

---

## Slide 4 — Seeing the six months as a picture

**This is your best slide. Slow down.**

**Say:** "Here is the same data drawn as a picture. Navy is customers who stayed, red is customers who left. Look at where they start — the same place. Now look at where they end."

**Then stop talking for two seconds.** Let them look. The picture does the work.

**Then:** "That is the whole finding. The two groups are not different in how much they spend. They are different in which direction they are going."

**The point to land:** direction, not level.

**Understand:** the lines actually cross at month one — the leavers start very slightly *above* the stayers. Notice it yourself before someone else does.

**If asked about the crossing** — "At the start of the window the two groups were indistinguishable, and the leavers were even marginally higher. That is exactly why no single month predicts anything."

**On the code panel:** "That is the function that produced the chart — it runs, it is in the repository." Do not walk through it line by line unless someone asks.

---

## Slide 5 — Turning six columns into one

**Say:** "A model reads columns literally and separately. It cannot see a direction spread across six columns, so I have to calculate it and hand it over as a single number."

**The point to land:** this is what feature engineering means. Not new data — making visible what was already there.

**Understand:** the reason the average fails. Two customers, one steady and one collapsing, can produce the identical average. The average keeps the level and throws away the direction — and the direction is the thing you need. Have that example ready; it is the clearest thirty seconds in the talk.

**If asked "why not give the model all six columns and let it work it out?"** — "I will test that. It may be able to. But handing it the direction directly means it does not have to discover it, and I get a number I can explain to a person."

---

## Slide 6 — Choosing how to measure the fall

**Say:** "There is no single correct way to measure a fall. So I built several versions and tested which separated the two groups best. They performed almost identically."

**The point to land:** you tested rather than picked, and you are reporting that the answer was boring.

**Understand:** this is a small slide that says something big about you — you check things even when you expect the answer not to matter, and you report the dull result honestly rather than dressing it up as a discovery.

**If asked "so which did you use?"** — "The one that uses all six months, so a single unusual month cannot distort it. I kept a simpler version alongside it for explaining results to people, because the model's number and the number you say out loud do not have to be the same."

---

## Slide 7 — Checking whether a column was cheating

**Say:** "One column worried me. When somebody closes their account, their salary stops arriving by definition. So if that column was recorded after they left, it would be describing the departure rather than predicting it."

**The point to land:** you went looking for a problem that would have made your results look *better*.

**Understand this properly, because it is the most technical thing in the deck.** The danger of leakage is that it disguises itself as success. A high score feels like proof you did well, so there is no natural moment where you would stop and doubt it.

**Explain the method, not just the result:** "I worked out what the data would look like if the worst case were true — nearly every leaver showing no salary arriving — and then checked whether it did. It did not. So the column is genuine."

**If asked "are you certain?"** — "No. The data is consistent with it being fine, but only the bank can tell me the date each column was recorded, and I have asked."

---

## Slide 8 — Two loan columns that turned out to be one

**Say:** "Two columns were saying the same thing. Everyone with a balance is marked as repaying, everyone without one is not — with no exceptions anywhere in the file."

**The point to land:** you noticed, checked, and made a reasoned choice about which to keep.

**Understand:** this is *not* leakage, and be ready to draw the distinction. Leakage is about time — a column knowing the future. This is about repetition — two columns saying one thing. Confusing them is common and getting it right is a good look.

**Why the balance survives:** "A yes-or-no flag can always be rebuilt from an amount. An amount can never be rebuilt from a flag. And the amount is what tells the agent how large an offer needs to be."

**If asked "could they be two different loans?"** — "That is what I checked. If they were, somebody would be repaying one loan while owing money on another. Nobody was."

---

## Slide 9 — An idea of mine that the data rejected

**Say this one confidently, not apologetically.**

**Say:** "I had a theory. Gender separates nobody overall, but I thought a married man with children might behave differently because of the responsibility he carries. Two columns can mean far more together than either does alone, so it seemed worth testing."

**Then:** "It was wrong. Once you know somebody's family situation, gender adds nothing."

**Then — and this is the part that matters:** "But what I was actually pointing at was responsibility, not gender. When I measured that directly, through marriage and children together, the pattern was clear. My idea was wrong about the variable and right about the mechanism, and it produced a column I would not otherwise have built."

**The point to land:** you test your own ideas and report the result even when it embarrasses you.

**Understand:** a rejected hypothesis is not a failure. Its value is being specific enough to test. This slide is the strongest evidence in the deck that your other findings can be trusted.

**If asked "would you have used gender if it had worked?"** — "No, and that is worth saying. Banking rules restrict using gender in decisions about credit and offers. It failed on two independent grounds and only one of them was statistical."

---

## Slide 10 — Not everyone leaves for the same reason

**Say:** "The people who leave are not one group. One is in financial difficulty — older, carrying a large loan, has missed payments, spending collapsing because they cannot afford it. The other is younger, has never missed a payment, is paid by a different bank and already holds a competitor's card. They were never really ours."

**The point to land:** the same risk score demands opposite actions.

**Say the line that makes it concrete:** "Help with debt is meaningless to somebody who is not struggling. Extra rewards are meaningless to somebody who cannot pay the loan they already have."

**Understand:** this is the slide that justifies the whole project. If one offer fitted everybody you would need a lookup table, not an agent. The fact that the right offer depends on *why* someone is leaving is the reason the system has to reason rather than look up.

**If asked "how do you tell them apart?"** — "Whether they have ever missed a loan payment separates them cleanly, and everything else about the two groups differs consistently after that."

---

## Slide 11 — Knowing what this data cannot tell me

**Say:** "A group of the people who left look identical to people who stayed on every column I have. Same age, same length of relationship, same credit score — and some were spending more than ever right up until they left."

**The point to land:** you know where your ceiling is and you are saying so before anyone finds it.

**Understand why this protects you.** When you eventually report your model's results, somebody will ask why you did not catch everyone. If you have already explained that a portion of leavers are invisible in this data, that question is answered. If you have not, it looks like a flaw you missed.

**Turn it into a recommendation:** "It also tells the bank what it is not recording — complaints, app activity, branch visits, and offers customers received from competitors. Those are the things that would explain the group I cannot see."

**Closing line:**

> "So that is where I am. I understand the data, I know what it can do and what it cannot, and I know which questions I still need answered. Next is building the columns and then the model."

---

## The five things to have ready

You will not be asked all of these, but knowing them means nothing catches you out.

| Question | Your answer |
|---|---|
| "What is the most important thing you found?" | Direction beats level. How much someone spends says little; whether it is rising or falling says a great deal. |
| "What would have gone wrong if you had rushed?" | Two things. The month ordering, which would have inverted every trend. And the salary column, which might have been describing departures rather than predicting them. |
| "What did you get wrong?" | My gender theory. I tested it, it failed, and it led me to a better column. |
| "How good will the model be?" | I do not know yet, and I would not guess. But I do know a share of leavers are undetectable in this data, so it will not catch everyone, and I can explain why. |
| "What do you need from us?" | Confirmation of when each column was recorded, what exactly counts as having left, and whether the credit limit can be included. |

---

## If it goes wrong

**If you blank:** go back to the one sentence. "I have not built anything yet — I have understood the data, including what it cannot do." Then pick up from whichever slide is on screen.

**If someone challenges a finding:** do not defend it. Ask what they would check, and write it down. Being interested in a challenge reads far better than being defensive about it.

**If you are asked something you have not thought about:** "That is a good question and I have not looked at that. I would check it by..." Then actually go and check it before the next meeting.
