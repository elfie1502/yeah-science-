# Your work

You are joining a project that already runs. Get it moving with the existing mouse controls first. Then take on the two sections below. The README has setup help and the protocol note explains the messages; neither assumes that you have used Qt before.

## Section 1: Better Call Git

Fork this repository, clone your fork and create a branch for your work. Read a little of the history and inspect a diff. Make commits that a teammate can follow, then open a pull request back to this repository. We will review the PR; you do not need to merge it.

There is some housekeeping to do:

- Decide which files are source, which are examples and which are generated during a run. Remove generated logs from Git tracking while retaining your local copies, and prevent future generated logs from appearing in `git status`. Keep useful fixtures and configuration examples.
- In a Linux terminal, find the entry point and configuration, launch the app, capture output in a file and locate a useful log message. The shell launcher has an executable-permission problem for you to resolve. `python -m app` works independently, so this does not block exploring the app.
- Briefly explain an important diff from your work and the commands that helped you investigate it.
- Suppose you accidentally committed to `main`. Explain how you would recover if the commit is only local, and how your approach changes after teammates have based work on a pushed commit. Keep shared history intact.
Ans:
Case 1 (Local Only): Run `git branch feature/my-work` to save current work on a new branch, then run `git reset --hard HEAD~1` to roll back main cleanly.
Case 2 (Remote/Pushed): Use `git revert <commit-hash>` to create a new safe commit that undoes the changes without rewriting shared public history.


## Section 2: Let Him Cook

### Add keyboard driving

The mouse pad already sends commands to the simulated rover. Add keyboard control through that same application path.

Expected behaviour:

- W/Up moves forward, S/Down reverses, A/Left turns left, D/Right turns right. Use the existing speed setting.
- Hold to move. Releasing the last movement key requests zero immediately, rather than waiting for the rover watchdog.
- Handle simultaneous keys deliberately. Opposing directions cancel; a forward/turn combination may curve or use a documented priority. Holding W and Up together must not double the speed or stop when only one is released.
- Key auto-repeat must not produce stuck movement.
- Losing window focus, disabling drive, disconnecting or opening Session notes clears keyboard input and requests a stop. Returning focus or closing the panel does not resume an old movement: require a fresh press.
- Typing in Session notes must not drive the rover. The mouse pad and STOP button must remain usable. STOP also clears any remembered keyboard movement.

Explain which input wins if mouse and keyboard overlap. Choose a clear policy and test it. You do not need to redesign the UI or rewrite the simulator.

### Investigate the connection indicator

Try these two reports:

1. Launch the app with no simulator running and click Connect. It reports a connection anyway.
2. Run both processes until telemetry arrives, then stop the simulator. The display still appears connected and keeps showing the old readings.

Investigate the cause and make the display tell the operator what is happening. Define useful states for disconnected, waiting for a first reply, receiving telemetry and stale telemetry. A valid telemetry message should be required to establish that the rover is replying; arbitrary incoming bytes are not enough.

Use the configured `stale_after_ms` threshold (1000 ms by default). Make old readings visibly stale or unavailable; zero is a possible real reading and should not stand in for missing data. Demonstrate recovery when valid telemetry resumes. Explain what your app does to drive input during telemetry loss; never silently resume an old held movement after recovery.

Use the `quiet`, `noise` and `dropout` scenarios in [protocol.md](protocol.md) to investigate. Add a repeatable regression check that fails on the original behaviour and passes with your change. The baseline tests cover existing behaviour, not all of these requirements.

### Explain your work

Help us follow one complete path from input to wheel command and back to the display. Show what you changed, how you checked it, where AI helped and what you still do not understand. A short recording, writing, slides or another clear explanation is fine. We care about whether you can help the next teammate work on it.

One further thought experiment: the app becomes sluggish during a field test. Before editing application code, what would you inspect to distinguish CPU load, growing memory use and communication trouble? Give your first few checks and what result would guide your next step. Look up command syntax as needed; you do not need ROS or a LiDAR for this question.

AI tools are welcome. You are responsible for checking their suggestions, but there is no requirement to manufacture an AI mistake or submit an entire chat transcript. If something is incomplete, explain what works and where you got stuck.
