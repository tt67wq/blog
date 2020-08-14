## Rob Pike's 5 Rules of Programming

Rule 1. You can't tell where a program is going to spend its time. Bottlenecks occur in surprising places, so don't try to second guess and put in a speed hack until you've proven that's where the bottleneck is.

Rule 2. Measure. Don't tune for speed until you've measured, and even then don't unless one part of the code overwhelms the rest.

Rule 3. Fancy algorithms are slow when n is small, and n is usually small. Fancy algorithms have big constants. Until you know that n is frequently going to be big, don't get fancy. (Even if n does get big, use Rule 2 first.)

Rule 4. Fancy algorithms are buggier than simple ones, and they're much harder to implement. Use simple algorithms as well as simple data structures.

Rule 5. Data dominates. If you've chosen the right data structures and organized things well, the algorithms will almost always be self-evident. Data structures, not algorithms, are central to programming. 

--------------

准则1: 你无法预测代码瓶颈。瓶颈会出现在你意想不到的地方，所以在你证明瓶颈在何处之前不要尝试做优化。

准则2: 测量。在有测量采样之前不要做性能优化，甚至你有了之后也不要做，除非此处是性能瓶颈。

准则3: 复杂的算法往往在n不大的时候性能不高，而n往往不会很大，除非你知道n会频繁的变大，否则不要使用复杂算法。(就算很大也别用，参考准则2)

准则3: 复杂算法更容易出bug，而且难以实现，所以最好使用简单算法和简单的数据结构。

准则4: 数据驱动。如果你选择了正确的数据结构，而且良好的组织了它们，那么算法往往水到渠成。数据结构才是编程的核心，而非算法。
