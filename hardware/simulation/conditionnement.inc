* PFE Combat Mirror - FlexiForce conditioning, one channel (ngspice)
* Shared by sim_dc.cir, sim_ac.cir and sim_tran.cir

* ---- Parameters -------------------------------------------------------
* SEL  : JP1 position (1 = sensitive, 2 = standard, 3 = high force)
* RSFS : sensor resistance at the full-scale force of the chosen mode
*        (hypothesis, to be replaced by the measured value)
.param SEL=2
.param RSFS=10k
.param VREFN={ternary_fcn(SEL==1, 1.03, ternary_fcn(SEL==2, 0.505, 0.103))}
* Feedback resistor for a 3.0 V full-scale output
.param RF={RSFS*(3.0/VREFN-1)}

* ---- Simplified rail-to-rail op-amp (MCP6004-like: 1 MHz GBW) ---------
* Pin order: in+ in- vdd vss out
.subckt opamp_rr inp inn vdd vss out
G1 0 n1 inp inn 1
R1 n1 0 1e5
C1 n1 0 159n
B1 o1 0 V = max(min(V(n1), V(vdd)-0.025), V(vss)+0.025)
Ro o1 out 25
.ends

* ---- Supply ------------------------------------------------------------
Vdd vdd 0 3.3

* ---- V_REF divider and JP1 ----------------------------------------------
R1 vdd tap1 22k
R2 tap1 tap2 5.1k
R3 tap2 tap3 3.9k
R4 tap3 0 1k
RJ1 tap1 vref {ternary_fcn(SEL==1, 1m, 1T)}
RJ2 tap2 vref {ternary_fcn(SEL==2, 1m, 1T)}
RJ3 tap3 vref {ternary_fcn(SEL==3, 1m, 1T)}
C1 vref 0 100n

* ---- Measurement channel -------------------------------------------------
XU1 vref nm vdd 0 o1 opamp_rr
* FlexiForce modelled as a conductance (in siemens) given by node g
Bfs nm 0 I = V(nm)*V(g)
RFX nm fb 1k
RV fb o1 {RF-1k}
* Anti-aliasing filter (fc ~ 480 Hz)
RO o1 adc 1k
CO adc 0 330n
