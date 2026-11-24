import assert from "node:assert/strict";
import {generate,validate} from "./scenario_engine_v4.mjs";
import {generateCommunications} from "./scenario_communication_generator_v1.mjs";
import {buildGroundTruth,validateGroundTruth} from "./scenario_ground_truth_v1.mjs";
const seeds=[0,1,7,19,42,2026,99173,4294967295];
const configs=[
 {organizations:1,dealsPerOrganization:1},
 {organizations:2,dealsPerOrganization:3},
 {organizations:5,dealsPerOrganization:6},
 {organizations:8,dealsPerOrganization:2}
];
const digest=x=>JSON.stringify(x);
const runs=[];
for(const seed of seeds){
 const w1=generate({seed}),w2=generate({seed});
 assert.deepEqual(w1,w2,"world is not reproducible for seed "+seed);
 assert.ok(validate(w1).pass,"world validation failed for seed "+seed);
 const c1=generateCommunications({seed}),c2=generateCommunications({seed});
 assert.deepEqual(c1.communications,c2.communications,"communications are not reproducible for seed "+seed);
 const g1=buildGroundTruth(c1),g2=buildGroundTruth(c2);
 assert.deepEqual(g1,g2,"ground truth is not reproducible for seed "+seed);
 assert.ok(validateGroundTruth(c1,g1).pass,"ground truth validation failed for seed "+seed);
 runs.push({seed,organizations:w1.organizations.length,deals:w1.deals.length,events:w1.events.length,communications:c1.communications.length});
}
const signatures=seeds.map(seed=>digest(generate({seed}).events));
assert.ok(new Set(signatures).size>1,"different seeds did not alter scenario outputs");
const configResults=[];
for(const config of configs){
 const a=generate({seed:42,...config}),b=generate({seed:42,...config});
 assert.deepEqual(a,b,"configuration is not reproducible: "+JSON.stringify(config));
 assert.equal(a.organizations.length,config.organizations);
 assert.equal(a.deals.length,config.organizations*config.dealsPerOrganization);
 assert.ok(validate(a).pass,"configured world failed validation");
 configResults.push({config,events:a.events.length});
}
for(const bad of [
 {seed:-1},{seed:1.5},{seed:NaN},{seed:4294967296},{organizations:0},{organizations:-1},
 {organizations:1.2},{dealsPerOrganization:0},{dealsPerOrganization:-1},
 {dealsPerOrganization:1.2}
]){
 assert.throws(()=>generate(bad),"invalid configuration accepted: "+JSON.stringify(bad));
}
const report={
 status:"PASS",seeds:runs,unique_seed_outputs:new Set(signatures).size,
 configurations:configResults,invalid_configurations_rejected:10,
 checks:["same-seed world replay","same-seed communication replay","same-seed ground-truth replay","different-seed variation","configuration reproducibility","world validation","ground-truth projection","invalid configuration rejection"]
};
console.log(JSON.stringify(report,null,2));
