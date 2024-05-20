 Hi everyone.
 I'm Karen. I've been an engineer here at Rox.
 for the past four years and I'm here with Nathan who...
 on zoom so I'll let Nathan introduce himself too.
 Hi, I don't know if you can see me yet.
 we can get that turned on. I wish I could be there, but I'm in the.
 the Roxas Boston office. So.
 Karen and I are going to talk to you today about how Rockset has...
 has combined disaggregated storage and fine green.
 replication in order to get a bunch of good properties.
 as we run prox TV in the cloud.
 So, Roxette is a real-time
 analytics in the cloud. So we run a bunch of nodes, we distribute.
 across them, store the data in RocksDB.
 updated by streaming data from a variety of sources.
 We have like, it could be like a Kafka events.
 It could be from a SQL database or.
 like Mongo or Dynamo, the things that come in.
 our JSON and unstructured and we store.
 and then we give you access to SQL on top of.
 So you can do joins and the full power of SQL.
 real time in this context means both low latency for up
 so we don't do any batching. We're basically like sending this stuff through as fast as we can.
 as we can. And as soon as data is ingested, it's immediately.
 visible to SQL.
 Real-time also means that if you have selective queries that the
 the queries are fast. So this is something where if you have a selective.
 query, you can wire it up to a UI and get like 100 milliseconds.
 latency or something like that. You can also run bigger.
 to take longer, but we kind of run the gamut.
 So the.
 in order to kind of explain the problem and...
 and how we've solved it. I wanna walk through kind of the.
 the evolution of rock sets architecture. So the...
 the kind of the garage stage or whatever of Roxette.
 was we do doc sharding across multiple.
 multiple nodes. Each of those.
 as a RocksDB instance inside and then we ingest data in and we also.
 run queries in that node. So there's a.
 actually a relatively complicated mapping between the incoming document.
 and the values, probably because we're.
 trying to store multiple indexes also because we can do transformations.
 and rollups during ingest. So like we want to, we want to.
 the intermediate results of the rollup.
 as we go along so they're always immediately available.
 This kind of naturally works and gives us our real...
 time nature because we're just writing to the mem table. And so the.
 queries kind of naturally immediately see it.
 So I mentioned we have this kind of.
 more complicated mapping.
 necessarily have to have a single key, RocksDB key value for us.
 single input document. If we do that.
 then we would call that a row store or document store. And we have.
 one of those, which is that's good if you have.
 particular document ID and you want to find all the stuff.
 also often doing scans, in which case we want to like a.
 columnar format, we encode that by taking.
 making a range of say 4,000 documents.
 and ripping out just a single...
 column from it and then storing that in a single ROCKsDB key.
 We also have inverted indexes. So we.
 we have whatever the value you're looking for and then a posting list of all.
 documents you would find. And then those things are grouped together also to...
 try to get good locality. And then when we run SQL, we have a full...
 like a normal rule-based optimizer and a cost.
 optimizer to try to figure out what the best.
 the best plan is.
 So back to this MVP. So what are the problems?
 So we have a fixed compute storage ratio.
 So that means that your most customers would either
 be overpaying for disk or overpaying for CPU.
 because you can't scale them independently.
 All of the CPU is happening in one place, so we don't get isolation.
 If you have a burst of ingest, then your queries might slow down.
 It's also if we're storing stuff on local, local.
 or local disk drives, then it's not very elastic.
 you have to do a lot of data movement when you're scaling. Like if you want to bring up a new node.
 then he needs to download the data from S3 or.
 or get it from somewhere else. That actually also.
 goes back to the efficiency because now if it takes a long time to bring up.
 a new node, you have to have a standby available all the time.
 So you have to have at least two copies on disk, not just one.
 And then also this particular style of just.
 having a single copy of the data.
 scaling limits. So we're doing leaf aggregator like doc sharding.
 to a leaf aggregation execution model, which...
 Which means that you eventually get scaling limits, especially if you're running a high QPL.
 like you don't want to be running a 10 millisecond.
 across 100 notes in the backend.
 So the first evolution in our.
 in our architecture was to move to disaggregated storage. So I'm excited to hear.
 the meta talk later about how they did it.
 The way that we did this is by
 like the only thing that lives in this.
 get his storage is SSD files. So we didn't really have to build.
 like a generic.
 file system because SSD files are relatively large and they're immutable.
 So you can kind of, it makes the problem.
 easier if you only solved that one. So we moved all the SSDs.
 the C files into the shared hot storage. And this is a
 a separate tier that's charted.
 and multi-tenant, it started differently than the upper.
 earlier, and this gives us a lot of advantages. So we can spin up.
 the new compute node quickly because the data is just kind of immediately available.
 Like we effectively have a global namespace for the files.
 We can be elastic like everyone.
 to like increase or decrease the size of a VI and, or the number.
 of nodes and move the shards around, that can be done pretty rapidly.
 It also gives us much faster failure recovery because we can use the ad.
 aggregate bandwidth of the entire storage cluster to replace a.
 old storage node. So we can replace a compute node easily because
 It doesn't have very much state and we can replace the storage nodes because we.
 we can just perform recovery. We can essentially remaster.
 the missing data onto all the rest of the storage cluster.
 And then now we've got orders of magnitude more down.
 download performance. For reference, if you're watching this,
 If you fill up the disk of an i3...
 Amazon node, it takes 48 minutes at full network bandwidth.
 with. So that's not something you can do fast enough.
 to maintain availability. But if you have 100.
 to those, then it goes a lot faster. And that's.
 even that's for full recovery. Like if you have some sort of.
 of notion of which data is more useful than you can get back online.
 almost immediately.
 Okay, so the next obvious evolution from there is to
 spin up multiple RocksDB instances accessing the same SSD file.
 because there's no reason why we can't access them from...
 multiple nodes simultaneously.
 actually launched this as a product and it's useful. The challenge here is this is.
 This is no longer real time. We're just accessing a snapshot. So if you want to.
 some sort of a nightly report that's not and have it not
 interfere with your online workload or your real-time workload.
 This is a good strategy, but it doesn't really.
 fulfill the full potential of.
 set. The thing that we're that we are talking about today
 is shared hot storage plus also do.
 fine-grain replication of the mem tables. So...
 This kind of ticks all of the dots. So what we have is.
 is, I think I've mixed my metaphors, but.
 You know what I mean? So what we have here is we have a.
 Show me to praise
 the instance, as soon as a change happens to its mem table, we can
 can immediately reflect that change in the mem table.
 instance of one or 10.
 RocksDB instances. We call these followers.
 This means that the queries that are running in those.
 in those virtual instances, are they're real.
 time now, they immediately see all the data.
 because the shared storage is shared amongst all of them.
 and we're maintaining physical replication at the ROXDB level.
 We only have to have a single copy of the data no matter how many.
 many of these compute, compute the eyes.
 you spin up. So we get the isolation that we want, we get the elastin.
 we want because we can just add them and remove them without having to.
 to affect the current workload.
 And because only the only.
 the leader has to do the injustice work. We actually also get...
 between the ingest work and the query CPU. So.
 So even if you don't take into account compaction, which also.
 only runs on the leader. The injustice process
 is typically 6x to 10x more.
 or I should say that the tailing the mem table.
 and applying it is about an order amounting to less work than being
 a full in just BI.
 Okay, so.
 I'm going to talk briefly about the shared hot storage and then Karen will tell you more.
 about the fine-grained replication. So.
 This is a RECTV Media.
 So I'm sure you've seen many slides.
 to talk about log structure merge trees before. The important point here.
 which I'm sure you're all aware of is that.
 We do big rights and we do asynchronous rights. So.
 the most cost effective.
 way to get durability when you're doing big rights.
 care how fast they are, is to write them to S3.
 So the right side of rocks.
 is not really affected at all by having the...
 having the need to do 64 meg writes and they take a couple
 milliseconds. It doesn't slow anything down. So that's great.
 The read side, however, especially for
 for Rockset is a little bit different. So,
 Rockset uses, sometimes we're doing scans and.
 sometimes we're doing index lookups. So if you're doing scans.
 then you're pulling a lot of data and you're mainly...
 are worried about throughput. Although it's.
 you have good clustering, then your scans kind of get a bit smaller.
 If you're doing index lookups, however, on the...
 the reads that you want to do are essentially IOP.
 We want to like we may be issuing.
 even only like a 4K read to the underlying store.
 that together and I think those
 S3 is not very good at 4k reads, I guess would be the the
 way to say it. So the idea is what we're going to do is
 is we're going to keep a copy of everything, but just one copy on.
 SDS and then we'll send the big rights to S3.
 that's the cheapest way to get durability and we'll send the small reads to.
 direct attach flash. And we're not even going to.
 use EBS here. We're actually going to use direct attach flash because that's the best way to
 get IOPS for small reads.
 Okay, so in this architecture.
 This looks kind of like a cache. If you have.
 a smaller faster thing in the front or maybe a more...
 expensive, less durable thing in the front and then a...
 a more.
 higher capacity, more durable thing in the back.
 The problem is that a cache list S3.
 is hundreds of milliseconds or can be and a cache hit.
 to our to our flash is on the order of hundreds of.
 microseconds. So it's like a thousand X difference.
 And 1000X is not something that we can handle on.
 on a regular basis in our real time.
 latency goal for our queries. So what we've done.
 is we've essentially built a cache and then we very care.
 carefully enumerated all the reasons why you might get a
 and works to get that number as close to.
 zero as possible. So some of these reasons are cold misses. So this is
 This is basically the first time you access something. It's never been in the cache.
 Capacity misses are when you run out of space and you have to throw something away.
 And then there's a variety of reasons why.
 You might've had something in cash, but then thrown it away or it's in the.
 wrong place because you resize the cluster or you had a failure or.
 or you did some sort of maybe it's there.
 you're in the middle of restarting the process for a software upgrade so it's effectively you're in the middle of restarting the process for a software upgrade so it's effectively you're in the middle of restarting the process for a software upgrade so it's effectively you're in the middle of restarting the process for a software upgrade so it's effectively you're in the middle of restarting the process for a software upgrade so it's effectively you're in the middle of restarting the process for a software upgrade so it's effectively you're in the middle of restarting the process for a software upgrade so it's effectively you're in the middle of restarting the process for a software upgrade so it's effectively you're in the middle of restarting the process for a software upgrade so it's effectively you're in the middle of restarting the process for a software upgrade so it's effectively you're in the middle of restarting the process for a software upgrade so it's effectively you're in the middle of restarting the process for a software upgrade so it's effectively
 available. Each of these things we have
 we've addressed. Now we have a.
 a blog post that actually goes into even more detail about this.
 I put the link at the bottom there.
 Basically what we're doing is we prefetch a graph.
 aggressively, we auto scale to avoid capacity misses.
 Although we actually still do run an LRU because that gives us
 kind of a soft landing, like if the autoscaler can't keep up.
 then the thing that we will not store on
 is the least useful thing rather than the most recently written thing.
 We have a dual.
 headed setup during roles. So we can actually have two different.
 server process is running simultaneously.
 accessing the same disk cache. So you can.
 seamlessly hand off from one to the other. You bring the new one up.
 and get it fully running and serving queries before you shut the old one down.
 And this means that there's a zero downtime.
 during the software role.
 And then we also, when we're doing resizing, we...
 Uh, we kind of keep track of where things were before and.
 And if we can't find it where we're looking for, we go check there first.
 before we go to S3. All of these things combined together.
 we operate so.
 99.9999 is usually like an ability
 That's actually the cache hit number.
 The technically, I guess the availability number for the system is.
 S3s, which they claim it's like a bazillion nines, but.
 Anyway, so we're essentially operating this thing as
 cash but trying to operate it in a zone where we never take a cash.
 We actually have an alarm that fires when we do take a cash.
 Okay, so that's the end of the presentation.
 That's kind of not that bad because SUD files are only written.
 slowly and they're immutable. There's not that many of them because they're really
 So it's kind of like, not too bad.
 On the other hand, doing fine.
 nine-grain replication of databases, this is kind of the deep end of the pool, right?
 You have like network partitions, you have...
 versions you have like if there's anybody here for meta they know what's
 me think is, if not, then you know what Paxos and Raft are.
 Anyway, so this is kind of a
 But this is a challenging topic. So I'm going to hand it over to Kiran, who's going to.
 tell us how we address these challenges.
 by solving them and partly by sidestepping some of them.
 Awesome.
 Hello. Okay, sorry.
 turned off. But yeah, thank you, Nathan, for the great introduction.
 So as Nathan mentioned, we're now in the deep.
 in the pool. But luckily there are a few components of
 of the RoXet system, which kind of act as floaties for us.
 and make it a bit easier to build a distributed replicate.
 system. And so I'll go into those in more detail.
 the next slide, but just to give a brief introduction.
 One important component is our input data stream.
 So that's actually both durable and persistent. And it functions.
 as a logical redo log that we can always replay from.
 Another important component is S3.
 provides durability of the RockCV instance contents.
 And lastly, we don't even worry about consensus.
 because we use an external metadata store to handle our leader.
 process.
 So the Rocksteady replication that we've built is
 something that we call leader follower. And it moves away from.
 replication to something that's much closer to physical replication.
 application. The idea is that for a given rock
 to be instance, you'll have multiple replicas. One replica.
 will be the leader and all of the others are the followers.
 The leader replica is responsible for data ingestion.
 So Nathan mentioned that as we ingest from the
 input data stream, we need to transform the input record.
 into the actual key value deltas that get applied to rocks.
 In addition, the leader will have to prop up a
 these fine grain rocks DB level updates to all of the followers.
 and from there the followers will maintain their
 local state for the Rock City instance.
 So because we have this shared hot storage tier, this means that our
 replicas are actually all physically identical at the store.
 layer. They share the exact same set of sst files.
 The only state that's updated logically is going to be the low.
 local state for the rocks to be instance. So the mem table that would.
 memory and then the local manifest file.
 So as a leader in jazz from the data stream, eventually.
 the memtable fills up and it has to flush it. So what
 happens here is with the memtiple flush.
 new sst file is generated the leader uploads it
 the shared hot storage tier and it tells the followers, hey, there's a
 new sst file. From there the followers can
 automatically use it if they need it and they can.
 basically act like they were the ones who generated it all along.
 So now looking at the other components in the Rocksat system.
 them, let's talk about the input data stream a bit more.
 So I mentioned that it functions as a durable logical.
 a redo log that we can always replay from. And what.
 this means is that we actually don't use the RockCB right ahead.
 because this gives us the same thing. So as a...
 and adjusting from the input stream.
 We also actually store our log position in this input stream.
 stream inside RocksDB itself under a key value pair that
 that gets updated atomically with the actual indexing changes.
 is associated with ingesting from that log record.
 And so this gives us a really nice property that, you know,
 you have your rocks to be instance and you always know where to start.
 tailing from in the input data stream to achieve exactly what we want.
 processing semantics there.
 Another important component of our system is the strongly consistent
 metadata store used for leader election.
 Of course, there's one leader replica. Everyone needs to know who it is.
 And so what we store in the metadata store is the identity of the leader.
 as well as this thing called a cookie.
 The cookie is composed of two parts. The first part.
 is the leadership epoch, so that's a sequence.
 the summer that gets bumped on every leadership change.
 And then the second part of the cookie is a random string.
 Another reason why we need to have randomness in the cookie is because we use it to
 to tolerate the case of multiple leaders running concurrently.
 And that could happen, for instance, there's like a
 and the old leader doesn't see that it should no longer
 they'll be running as a leader. And so in this time, you'll see that the
 would have the old leader and the new leader both functioning as a leader.
 And so what we do with the cookie is we make sure the cookie is
 included in all the files written to S3 in the file name.
 and so that way two leaders can run at the same time.
 without clobbering each other's state in S3.
 So now let's look at how we would.
 Ruth Strump, a leader in our system. So if you're a replica and you want to be.
 leader. The first thing you would do is you'd go to the metadata store.
 to read the cookie and using that you can fetch
 a recent RocksDB snapshot in S3.
 using that as a starting point, you'll generate a new ROCKSDB style.
 snapshot with a new cookie and then write that to S3.
 Once you've successfully uploaded the new stop chart to S3
 to actually install yourself as the leader, you'd go.
 back to the metadata store and perform a compare and swap.
 Because we use a compare and swap, this means that for
 a given leadership at POC exactly one replica.
 will win the election. And so if you do win, that's a good thing.
 great it's time to do some real work. So then...
 As you remember, we mentioned that in the rock
 to be insisted itself, we store the log position where you need to start tailoring.
 from the input data stream.
 So as the leader in just from the input data stream.
