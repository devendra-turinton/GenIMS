# GenIMS Fault Pattern Library

## Overview
This document defines realistic fault patterns for different machine and sensor types in the auto parts manufacturing environment. Each pattern describes the signature characteristics that can be used to detect and predict failures.

---

## 1. BEARING FAILURES

### Pattern: Bearing Degradation
**Machine Types:** CNC machines, grinding machines, rotating equipment  
**Primary Sensor:** Vibration  
**Fault Code:** BEAR-001  
**Severity:** Critical  
**Typical Duration:** 7-21 days from first detection to failure

#### Signature Characteristics:
1. **Vibration Pattern:**
   - Normal: 5-15 mm/s
   - Warning starts: 15-20 mm/s (gradual increase over 3-7 days)
   - Critical: 20-40 mm/s (rapid increase over 24-48 hours)
   - Failure: >40 mm/s

2. **Temperature Pattern:**
   - Correlated temperature rise
   - Normal: 40-60°C
   - Warning: 60-75°C
   - Critical: 75-90°C
   - Failure: >90°C

3. **Noise Pattern:**
   - Increased high-frequency noise
   - Grinding or squealing sounds

4. **Performance Impact:**
   - Cycle time increases by 5-15%
   - Surface finish quality degrades
   - Increased power consumption (+10-20%)

#### Detection Query:
```sql
-- Bearing failure early warning
SELECT m.machine_id, m.machine_name, 
       MAX(sd.measurement_value) as max_vibration,
       AVG(sd.measurement_value) as avg_vibration
FROM sensor_data sd
JOIN sensors s ON sd.sensor_id = s.sensor_id
JOIN machines m ON s.machine_id = m.machine_id
WHERE s.sensor_type = 'vibration'
  AND sd.timestamp > NOW() - INTERVAL '24 hours'
  AND sd.measurement_value > 15
GROUP BY m.machine_id, m.machine_name
HAVING AVG(sd.measurement_value) > 18
ORDER BY max_vibration DESC;
```

---

## 2. MOTOR OVERHEATING

### Pattern: Thermal Overload
**Machine Types:** All machines with electric motors  
**Primary Sensor:** Temperature, Current  
**Fault Code:** THERM-001  
**Severity:** Major  
**Typical Duration:** 30 minutes to 4 hours

#### Signature Characteristics:
1. **Temperature Pattern:**
   - Rapid rise: 5-10°C per 30 minutes
   - Normal: 45-70°C
   - Warning: 70-85°C
   - Critical: 85-100°C
   - Auto-shutdown: >100°C

2. **Current Pattern:**
   - Normal: 80-90% of rated current
   - Overload: 90-110% of rated current
   - Critical: >110% (thermal trip imminent)

3. **Duty Cycle:**
   - Extended high-load operation (>80% duty cycle for >2 hours)
   - Insufficient cooling periods

4. **Performance Impact:**
   - Reduced torque output
   - Increased cycle times
   - Automatic thermal protection triggers

#### Detection Query:
```sql
-- Motor overheating detection
SELECT m.machine_id, m.machine_name,
       temp.measurement_value as current_temp,
       curr.measurement_value as current_draw,
       smd.power_consumption_kw
FROM machines m
JOIN sensor_data temp ON temp.machine_id = m.machine_id
JOIN sensors s1 ON temp.sensor_id = s1.sensor_id AND s1.sensor_type = 'temperature'
JOIN sensor_data curr ON curr.machine_id = m.machine_id
JOIN sensors s2 ON curr.sensor_id = s2.sensor_id AND s2.sensor_type = 'current'
JOIN scada_machine_data smd ON smd.machine_id = m.machine_id
WHERE temp.timestamp = (SELECT MAX(timestamp) FROM sensor_data WHERE sensor_id = s1.sensor_id)
  AND curr.timestamp = (SELECT MAX(timestamp) FROM sensor_data WHERE sensor_id = s2.sensor_id)
  AND temp.measurement_value > 70
  AND curr.measurement_value > 360
ORDER BY temp.measurement_value DESC;
```

---

## 3. HYDRAULIC PRESSURE LOSS

### Pattern: Hydraulic System Degradation
**Machine Types:** Presses, forming machines, injection molding  
**Primary Sensor:** Pressure, Flow  
**Fault Code:** HYD-001  
**Severity:** Major  
**Typical Duration:** Sudden (minutes) or Gradual (days to weeks)

#### Signature Characteristics:
1. **Pressure Pattern (Sudden Leak):**
   - Rapid drop: Normal to critical in <5 minutes
   - Normal: 120-150 bar
   - Warning: 100-120 bar
   - Critical: <100 bar
   - System shutdown: <80 bar

2. **Pressure Pattern (Gradual Degradation):**
   - Slow decline: 2-5 bar per day
   - Increased pressure fluctuations (±10 bar)
   - Difficulty maintaining setpoint

3. **Flow Rate Changes:**
   - Reduced flow rate (proportional to pressure loss)
   - Increased pump cycles

4. **Performance Impact:**
   - Reduced press force/tonnage
   - Inconsistent part quality
   - Increased cycle times (10-25%)
   - Increased energy consumption

#### Detection Query:
```sql
-- Hydraulic pressure anomaly detection
SELECT m.machine_id, m.machine_name,
       s.sensor_id, s.sensor_name,
       sd.measurement_value as current_pressure,
       sd.avg_value_1min,
       sd.std_dev_1min,
       s.normal_operating_min,
       s.normal_operating_max
FROM sensor_data sd
JOIN sensors s ON sd.sensor_id = s.sensor_id
JOIN machines m ON s.machine_id = m.machine_id
WHERE s.sensor_type = 'pressure'
  AND sd.timestamp > NOW() - INTERVAL '1 hour'
  AND (sd.measurement_value < s.normal_operating_min 
       OR sd.std_dev_1min > 10)
ORDER BY sd.timestamp DESC;
```

---

## 4. TOOL WEAR

### Pattern: Cutting Tool Degradation
**Machine Types:** CNC mills, lathes, drilling machines  
**Primary Sensor:** Vibration, Current, Force  
**Fault Code:** TOOL-001  
**Severity:** Minor to Major  
**Typical Duration:** Hours to days depending on material and tool

#### Signature Characteristics:
1. **Vibration Pattern:**
   - Gradual increase in high-frequency components
   - Normal: 8-12 mm/s
   - Worn: 12-18 mm/s
   - Critical: >18 mm/s

2. **Cutting Force/Current:**
   - Increased current draw: +15-30%
   - Higher cutting forces
   - More erratic force patterns

3. **Surface Finish:**
   - Degraded surface quality (Ra value increases)
   - Burr formation
   - Dimensional inaccuracy

4. **Performance Impact:**
   - Slower feed rates required
   - More frequent tool changes
   - Increased scrap rate (5-20%)
   - Extended cycle times

#### Detection Query:
```sql
-- Tool wear detection
SELECT m.machine_id, m.machine_name,
       smd.tool_number,
       AVG(sd.measurement_value) as avg_vibration,
       MAX(sd.measurement_value) as max_vibration,
       COUNT(*) as readings_count
FROM scada_machine_data smd
JOIN sensor_data sd ON sd.machine_id = smd.machine_id
JOIN sensors s ON sd.sensor_id = s.sensor_id
WHERE s.sensor_type = 'vibration'
  AND smd.machine_state = 'running'
  AND sd.timestamp > NOW() - INTERVAL '4 hours'
GROUP BY m.machine_id, m.machine_name, smd.tool_number
HAVING AVG(sd.measurement_value) > 12
ORDER BY avg_vibration DESC;
```

---

## 5. WELDING QUALITY DEGRADATION

### Pattern: Weld Quality Issues
**Machine Types:** Spot welders, arc welders, laser welders  
**Primary Sensor:** Current, Voltage, Force (for spot welding)  
**Fault Code:** WELD-001  
**Severity:** Major (quality issue)  
**Typical Duration:** Immediate or gradual over shift

#### Signature Characteristics:
1. **Current Pattern (Spot Welding):**
   - Inconsistent current: ±15% variation
   - Normal: 8-12 kA
   - Low quality: <7 kA or >13 kA
   - Electrode wear causes current increase

2. **Voltage Pattern (Arc Welding):**
   - Unstable arc voltage
   - Normal: 24-28V
   - Poor quality: <20V or >32V

3. **Force Pattern (Spot Welding):**
   - Insufficient electrode force
   - Normal: 3-5 kN
   - Low quality: <2.5 kN

4. **Performance Impact:**
   - Weak weld joints
   - Increased rework rate (10-40%)
   - Failed leak tests
   - Customer quality complaints

#### Detection Query:
```sql
-- Welding quality anomaly
SELECT m.machine_id, m.machine_name,
       s.sensor_type,
       AVG(sd.measurement_value) as avg_value,
       STDDEV(sd.measurement_value) as std_deviation,
       COUNT(*) as weld_count
FROM sensor_data sd
JOIN sensors s ON sd.sensor_id = s.sensor_id
JOIN machines m ON s.machine_id = m.machine_id
WHERE m.machine_type LIKE '%weld%'
  AND s.sensor_type IN ('current', 'voltage', 'force')
  AND sd.timestamp > NOW() - INTERVAL '8 hours'
GROUP BY m.machine_id, m.machine_name, s.sensor_type
HAVING STDDEV(sd.measurement_value) > (AVG(sd.measurement_value) * 0.15)
ORDER BY std_deviation DESC;
```

---

## 6. PNEUMATIC SYSTEM FAILURE

### Pattern: Air Pressure/Flow Issues
**Machine Types:** Assembly stations, pick-and-place robots, actuators  
**Primary Sensor:** Pressure, Flow  
**Fault Code:** PNEU-001  
**Severity:** Minor to Major  
**Typical Duration:** Minutes to hours

#### Signature Characteristics:
1. **Pressure Pattern:**
   - Slow leak: -0.5 bar per hour
   - Rapid leak: Normal to zero in <10 minutes
   - Normal: 5-7 bar
   - Warning: 4-5 bar
   - Critical: <4 bar

2. **Flow Rate:**
   - Increased flow (leak present)
   - Cyclic pressure drops (actuator cycles)

3. **Performance Impact:**
   - Slower actuator speeds
   - Incomplete cycles
   - Position errors
   - Assembly quality issues

#### Detection Query:
```sql
-- Pneumatic pressure issues
SELECT m.machine_id, m.machine_name,
       sd.measurement_value as current_pressure,
       sd.min_value_1min,
       sd.avg_value_1min,
       (s.normal_operating_min - sd.avg_value_1min) as pressure_deficit
FROM sensor_data sd
JOIN sensors s ON sd.sensor_id = s.sensor_id
JOIN machines m ON s.machine_id = m.machine_id
WHERE s.sensor_type = 'pressure'
  AND s.measurement_unit = 'bar'
  AND sd.timestamp > NOW() - INTERVAL '30 minutes'
  AND sd.avg_value_1min < s.normal_operating_min
ORDER BY pressure_deficit DESC;
```

---

## 7. COOLANT SYSTEM FAILURE

### Pattern: Coolant Flow/Temperature Issues
**Machine Types:** CNC machines, grinding machines  
**Primary Sensor:** Temperature, Flow  
**Fault Code:** COOL-001  
**Severity:** Major  
**Typical Duration:** Minutes to hours

#### Signature Characteristics:
1. **Temperature Pattern:**
   - Rapid rise due to insufficient cooling
   - Normal coolant temp: 20-25°C
   - High coolant temp: 25-35°C
   - Critical: >35°C
   - Spindle/workpiece temp increases by 10-20°C

2. **Flow Rate:**
   - Reduced or zero flow
   - Normal: 40-80 L/min
   - Low: 20-40 L/min
   - Critical: <20 L/min

3. **Performance Impact:**
   - Tool life reduced by 30-60%
   - Poor surface finish
   - Thermal expansion issues
   - Dimensional inaccuracy

#### Detection Query:
```sql
-- Coolant system monitoring
SELECT m.machine_id, m.machine_name,
       temp.measurement_value as coolant_temp,
       flow.measurement_value as flow_rate,
       smd.temperature_actual_c as machine_temp
FROM machines m
JOIN sensor_data temp ON temp.machine_id = m.machine_id
JOIN sensors s1 ON temp.sensor_id = s1.sensor_id AND s1.sensor_type = 'temperature'
JOIN sensor_data flow ON flow.machine_id = m.machine_id
JOIN sensors s2 ON flow.sensor_id = s2.sensor_id AND s2.sensor_type = 'flow'
JOIN scada_machine_data smd ON smd.machine_id = m.machine_id
WHERE temp.timestamp > NOW() - INTERVAL '10 minutes'
  AND flow.timestamp > NOW() - INTERVAL '10 minutes'
  AND (temp.measurement_value > 30 OR flow.measurement_value < 30)
ORDER BY temp.measurement_value DESC;
```

---

## 8. ROBOT ARM POSITIONING ERROR

### Pattern: Servo Motor/Encoder Issues
**Machine Types:** Industrial robots, pick-and-place systems  
**Primary Sensor:** Position (displacement), Current  
**Fault Code:** ROBO-001  
**Severity:** Major  
**Typical Duration:** Sudden or gradual over days

#### Signature Characteristics:
1. **Position Error:**
   - Increasing position deviation
   - Normal accuracy: ±0.05 mm
   - Warning: ±0.1-0.5 mm
   - Critical: >±0.5 mm

2. **Repeatability:**
   - Reduced repeatability
   - Position varies cycle-to-cycle

3. **Current Draw:**
   - Erratic current patterns
   - Higher current to maintain position

4. **Performance Impact:**
   - Assembly errors
   - Part placement issues
   - Quality rejections
   - Increased cycle time

#### Detection Query:
```sql
-- Robot positioning accuracy
SELECT m.machine_id, m.machine_name,
       s.sensor_name,
       AVG(sd.measurement_value) as avg_position,
       STDDEV(sd.measurement_value) as position_variance,
       MAX(ABS(sd.measurement_value - s.normal_operating_max/2)) as max_deviation
FROM sensor_data sd
JOIN sensors s ON sd.sensor_id = s.sensor_id
JOIN machines m ON s.machine_id = m.machine_id
WHERE m.machine_type LIKE '%robot%'
  AND s.sensor_type = 'displacement'
  AND sd.timestamp > NOW() - INTERVAL '2 hours'
GROUP BY m.machine_id, m.machine_name, s.sensor_id, s.sensor_name
HAVING STDDEV(sd.measurement_value) > 0.5
ORDER BY position_variance DESC;
```

---

## 9. ELECTRICAL FAULT

### Pattern: Power Supply/Motor Controller Issues
**Machine Types:** All machines  
**Primary Sensor:** Voltage, Current  
**Fault Code:** ELEC-001  
**Severity:** Critical  
**Typical Duration:** Sudden (milliseconds to seconds)

#### Signature Characteristics:
1. **Voltage Pattern:**
   - Voltage sag: <90% nominal
   - Voltage swell: >110% nominal
   - Normal: 380-420V (3-phase)
   - Warning: 360-380V or 420-440V
   - Critical: <360V or >440V

2. **Current Pattern:**
   - Overcurrent: >120% rated
   - Phase imbalance: >10% difference
   - Ground fault: leakage current

3. **Performance Impact:**
   - Unexpected shutdowns
   - Equipment damage risk
   - Safety hazard
   - Production stoppage

#### Detection Query:
```sql
-- Electrical anomaly detection
SELECT m.machine_id, m.machine_name,
       volt.measurement_value as voltage,
       curr.measurement_value as current_draw,
       volt.is_above_critical OR volt.is_below_critical as voltage_critical,
       curr.is_above_critical as overcurrent
FROM machines m
JOIN sensor_data volt ON volt.machine_id = m.machine_id
JOIN sensors s1 ON volt.sensor_id = s1.sensor_id AND s1.sensor_type = 'voltage'
JOIN sensor_data curr ON curr.machine_id = m.machine_id
JOIN sensors s2 ON curr.sensor_id = s2.sensor_id AND s2.sensor_type = 'current'
WHERE volt.timestamp > NOW() - INTERVAL '5 minutes'
  AND curr.timestamp > NOW() - INTERVAL '5 minutes'
  AND (volt.is_above_critical OR volt.is_below_critical OR curr.is_above_critical)
ORDER BY volt.timestamp DESC;
```

---

## 10. SENSOR DRIFT/FAILURE

### Pattern: Sensor Calibration Issues
**Machine Types:** All machines  
**Primary Indicator:** Sensor health metrics  
**Fault Code:** SENS-001  
**Severity:** Minor to Major  
**Typical Duration:** Days to weeks

#### Signature Characteristics:
1. **Drift Pattern:**
   - Gradual offset from expected range
   - Comparison with redundant sensors shows divergence
   - Drift: 2-5% per month

2. **Stuck Value:**
   - Same reading for extended period
   - No response to process changes

3. **Erratic Readings:**
   - Wild fluctuations inconsistent with process
   - High standard deviation

4. **Communication Issues:**
   - Packet loss >5%
   - Intermittent connectivity
   - Timestamp gaps

#### Detection Query:
```sql
-- Sensor health issues
SELECT s.sensor_id, s.sensor_name, m.machine_name,
       sh.health_score,
       sh.drift_percentage,
       sh.stuck_value_detected,
       sh.erratic_readings_detected,
       sh.days_since_calibration,
       sh.overall_status
FROM sensor_health sh
JOIN sensors s ON sh.sensor_id = s.sensor_id
JOIN machines m ON s.machine_id = m.machine_id
WHERE sh.timestamp > NOW() - INTERVAL '1 hour'
  AND (sh.health_score < 70 
       OR sh.stuck_value_detected = true 
       OR sh.erratic_readings_detected = true
       OR sh.drift_percentage > 5)
ORDER BY sh.health_score ASC;
```

---

## FAULT PATTERN MATRIX

| Fault Pattern | Machine Types | Primary Sensors | Severity | Lead Time | Detectability |
|--------------|---------------|-----------------|----------|-----------|---------------|
| Bearing Failure | Rotating equipment | Vibration, Temp | Critical | 7-21 days | High |
| Motor Overheating | All motors | Temp, Current | Major | 30min-4hr | High |
| Hydraulic Loss | Presses, forming | Pressure, Flow | Major | Sudden/Days | High |
| Tool Wear | CNC, machining | Vibration, Current | Minor-Major | Hours-Days | Medium |
| Welding Issues | Welders | Current, Voltage | Major | Immediate | Medium |
| Pneumatic Failure | Assembly, robots | Pressure | Minor-Major | Minutes-Hours | High |
| Coolant Failure | Machining | Temp, Flow | Major | Minutes-Hours | High |
| Robot Positioning | Robots | Displacement | Major | Sudden/Days | Medium |
| Electrical Fault | All machines | Voltage, Current | Critical | Sudden | High |
| Sensor Drift | All machines | Health metrics | Minor-Major | Days-Weeks | Medium |

---

## DATA GENERATION GUIDELINES

### For Realistic Fault Simulation:

1. **Normal Operation (80% of time):**
   - Values within normal operating range
   - Small random variations (±2-5%)
   - Occasional minor deviations

2. **Warning Conditions (15% of time):**
   - Values approaching threshold limits
   - Increased variability
   - Gradual trending toward fault

3. **Fault Conditions (5% of time):**
   - Values exceeding critical thresholds
   - Rapid changes or sustained deviations
   - Multiple correlated sensor anomalies

4. **Fault Progression:**
   - Bearing: 7-14 days gradual, then 24-48 hours rapid
   - Overheating: 30-120 minutes gradual increase
   - Hydraulic: 5-30 minutes sudden OR 7-14 days gradual
   - Tool wear: 4-8 hours gradual
   - Electrical: Sudden (seconds)

---

## PREDICTIVE MAINTENANCE RULES

### Rule-Based Detection Thresholds:

1. **Single Sensor Critical:**
   - Any sensor exceeds critical threshold → Immediate alert
   - Sustained warning threshold (>15 min) → Warning alert

2. **Multi-Sensor Correlation:**
   - Vibration + Temperature both elevated → Bearing warning
   - Current + Temperature + Vibration → Motor overload warning
   - Pressure drop + Flow increase → Hydraulic leak

3. **Trend Analysis:**
   - 20% increase over 7 days → Gradual degradation
   - 50% increase over 24 hours → Rapid degradation
   - Exponential trend → Imminent failure

4. **Statistical Anomaly:**
   - Value >3 standard deviations from mean → Anomaly
   - Sustained deviation (>30 min) → Fault condition

---

## QUERY EXAMPLES FOR FAULT DETECTION

### Multi-Machine Health Dashboard:
```sql
WITH machine_health AS (
  SELECT 
    m.machine_id,
    m.machine_name,
    m.criticality,
    smd.machine_state,
    COUNT(DISTINCT CASE WHEN sd.is_anomaly THEN sd.sensor_id END) as anomaly_sensors,
    MAX(CASE WHEN s.sensor_type = 'vibration' THEN sd.measurement_value END) as max_vibration,
    MAX(CASE WHEN s.sensor_type = 'temperature' THEN sd.measurement_value END) as max_temperature,
    AVG(smd.oee_percentage) as avg_oee
  FROM machines m
  LEFT JOIN scada_machine_data smd ON m.machine_id = smd.machine_id
  LEFT JOIN sensor_data sd ON m.machine_id = sd.machine_id
  LEFT JOIN sensors s ON sd.sensor_id = s.sensor_id
  WHERE smd.timestamp > NOW() - INTERVAL '1 hour'
    AND sd.timestamp > NOW() - INTERVAL '1 hour'
  GROUP BY m.machine_id, m.machine_name, m.criticality, smd.machine_state
)
SELECT 
  machine_id,
  machine_name,
  criticality,
  machine_state,
  anomaly_sensors,
  CASE 
    WHEN anomaly_sensors >= 3 THEN 'CRITICAL'
    WHEN anomaly_sensors >= 2 THEN 'WARNING'
    WHEN max_vibration > 20 OR max_temperature > 85 THEN 'WARNING'
    WHEN avg_oee < 70 THEN 'ATTENTION'
    ELSE 'NORMAL'
  END as health_status
FROM machine_health
ORDER BY 
  CASE health_status
    WHEN 'CRITICAL' THEN 1
    WHEN 'WARNING' THEN 2
    WHEN 'ATTENTION' THEN 3
    ELSE 4
  END,
  criticality DESC;
```

This fault pattern library provides the foundation for generating realistic operational data and implementing predictive maintenance algorithms in GenIMS.
