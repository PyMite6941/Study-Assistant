# Computer Science Notes

## Algorithms and Complexity

An algorithm is a step-by-step procedure for solving a problem. A good algorithm is correct, efficient, and clearly defined.

Big O notation describes how an algorithm's runtime or space grows with input size. O(1) is constant time, O(log n) is logarithmic, O(n) is linear, O(n²) is quadratic.

Binary search runs in O(log n) time. It works on sorted arrays by repeatedly halving the search space. It is far more efficient than linear search O(n) for large datasets.

Sorting algorithms: Bubble sort is O(n²) — simple but slow. Merge sort is O(n log n) — divides the array in half recursively then merges. Quick sort is O(n log n) average but O(n²) worst case.

A greedy algorithm makes the locally optimal choice at each step hoping to find a global optimum. It works well for problems like Dijkstra's shortest path but not all optimization problems.

Dynamic programming solves problems by breaking them into overlapping subproblems and storing results to avoid recomputation (memoization). Examples: Fibonacci sequence, knapsack problem.

## Data Structures

An array stores elements in contiguous memory locations. Access is O(1) but insertion and deletion are O(n) because elements must shift.

A linked list stores elements as nodes where each node points to the next. Insertion and deletion are O(1) at known positions but access is O(n).

A stack follows Last In First Out (LIFO). Operations are push (add) and pop (remove). Used in function call stacks and undo operations.

A queue follows First In First Out (FIFO). Operations are enqueue (add) and dequeue (remove). Used in scheduling and breadth-first search.

A hash table stores key-value pairs. It uses a hash function to compute an index. Average O(1) for insert, delete, and lookup. Collisions are handled by chaining or open addressing.

A binary tree is a hierarchical structure where each node has at most two children. A binary search tree (BST) keeps left children smaller and right children larger, enabling O(log n) search.

Graphs consist of vertices (nodes) and edges. They can be directed or undirected, weighted or unweighted. Used to model networks, maps, and relationships.

## Programming Concepts

Object-oriented programming (OOP) organizes code into objects that combine data (attributes) and behavior (methods). The four pillars are encapsulation, abstraction, inheritance, and polymorphism.

Encapsulation hides internal state and requires all interaction through methods. Inheritance allows a class to inherit properties from a parent class. Polymorphism allows different classes to be treated through the same interface.

Recursion is when a function calls itself. Every recursive function needs a base case to stop the recursion and a recursive case to make progress toward it.

A variable is a named storage location. A function is a reusable block of code. Parameters are inputs to a function; return values are its outputs.

Compiled languages (e.g., C, C++) translate code to machine code before execution. Interpreted languages (e.g., Python, JavaScript) translate code at runtime. Compiled code is generally faster.

## Networking

The Internet is a global network of interconnected computers. Data travels in packets — small chunks that are reassembled at the destination.

The TCP/IP model is the foundation of internet communication. TCP (Transmission Control Protocol) ensures reliable delivery. IP (Internet Protocol) handles addressing and routing.

An IP address uniquely identifies a device on a network. IPv4 uses 32-bit addresses (e.g., 192.168.1.1). IPv6 uses 128-bit addresses to accommodate more devices.

DNS (Domain Name System) translates human-readable domain names (e.g., google.com) into IP addresses. It acts as the internet's phone book.

HTTP (HyperText Transfer Protocol) is used for transferring web pages. HTTPS adds SSL/TLS encryption for security. Common HTTP methods are GET (retrieve), POST (send), PUT (update), DELETE (remove).

A firewall monitors and filters incoming and outgoing network traffic based on security rules. It protects networks from unauthorized access.

## Databases

A relational database stores data in tables with rows and columns. Tables are linked by foreign keys. SQL (Structured Query Language) is used to query and manipulate data.

Key SQL commands: SELECT retrieves data, INSERT adds records, UPDATE modifies records, DELETE removes records, JOIN combines data from multiple tables.

Normalization is the process of organizing a database to reduce redundancy. First normal form (1NF) eliminates duplicate columns. Second (2NF) and third (3NF) normal forms further reduce redundancy.

NoSQL databases store data in formats other than tables — document stores (MongoDB), key-value stores (Redis), column stores (Cassandra), and graph databases (Neo4j). They are useful for unstructured or rapidly changing data.

ACID properties ensure reliable database transactions: Atomicity (all or nothing), Consistency (data remains valid), Isolation (transactions don't interfere), Durability (committed data persists).

## Operating Systems

An operating system (OS) manages hardware resources and provides services for programs. Examples include Windows, macOS, Linux, and Android.

A process is a running instance of a program. The OS scheduler decides which process runs and when. Multitasking allows multiple processes to run concurrently by rapidly switching between them.

Virtual memory allows the OS to use disk space as an extension of RAM. It gives programs the illusion of more memory than physically exists.

A file system organizes how data is stored and retrieved on storage devices. Common file systems include NTFS (Windows), ext4 (Linux), and APFS (macOS).

Deadlock occurs when two or more processes are each waiting for the other to release a resource, causing all to be stuck indefinitely.
