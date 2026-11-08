# Open questions

- Member discount and coupon TEN both qualify: do they stack, and in what order? CHANGELOG.md 0.3.0 says "stack, TEN
  first", but it is not an accepted decision in DECISIONS.md. Code raises NotSpecified.
- How is the 10% member discount rounded when it is a fraction of a cent? The pricing.py skeleton comment says "round
  half up", but it is not an accepted decision. Code raises NotSpecified.
- Do cancelled lines count toward loyalty points and the 10-item bonus? NOTES.md (standup 11/6, Sam) says no, but it
  is not an accepted decision. Code raises NotSpecified.
