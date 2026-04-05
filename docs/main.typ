#import "figures.typ"
#import "template.typ"
#show: template.init
#set document(
  author: "心悸媽咪",
  keywords: ("ECG", "Raspberry Pi 3B", "ESP32", "AF detect", "MLP", "Cat Boost", "Pan-Tompkins++"),
  title: [心悸寶貝--作品企劃書],
)

#show: template.toc

= Motivation and Objectives 
#h(2em) Cardiovascular diseases (CVDs) remain the leading cause of mortality worldwide, highlighting the critical need for effective continuous monitoring and early detection. Recent advances in wearable technologies have made electrocardiogram (ECG) monitoring increasingly accessible in daily life.

However, *most existing wearable ECG systems are limited to short-duration recordings*, typically around one minute, and provide only basic real-time analysis, such as heart rate estimation. While some devices support arrhythmia detection, their functionality is often primarily limited to detecting persistent atrial fibrillation (AF), without the capability to identify more complex or transient conditions.

Atrial fibrillation (AF) is commonly classified into paroxysmal, persistent, and permanent forms according to episode duration and termination behavior @markides2003atrial. Paroxysmal AF refers to episodes that terminate spontaneously, typically within several days, whereas persistent and permanent AF require clinical intervention or cannot be terminated. Due to its intermittent nature, *paroxysmal AF is particularly challenging to detect using conventional short-duration monitoring systems*, and such episodes are therefore frequently missed. This limitation is critical, as early detection of transient arrhythmias and comprehensive cardiovascular risk assessment are essential for timely medical intervention and long-term disease prevention.

Therefore, we propose an *integrated framework that enables long-term ECG monitoring* and incorporates two components: an *atrial fibrillation detection module* and a *cardiovascular disease prediction model*. The AF detection module focuses on identifying both paroxysmal and persistent atrial fibrillation from continuous ECG signals, while the cardiovascular disease prediction model provides a comprehensive assessment of cardiovascular conditions based on extracted features. Our proposed system offers a more complete solution for both real-time arrhythmia detection and cardiovascular risk evaluation.

= System Design
== Key Innovations
#h(2em)The proposed system introduces a unified framework for continuous ECG monitoring and analysis, integrating long-term data acquisition, real-time signal processing, and edge-based inference. Its key features are summarized as follows:
- *Interpretable physiological indicators*: The system incorporates cardiovascular risk assessment derived from ECG features, transforming raw signals into meaningful and interpretable outputs accessible to non-specialist users. In addition, it supports the export of ECG signal plots to facilitate subsequent review by healthcare professionals.
- *Long-term continuous monitoring*: Supports sustained ECG acquisition beyond the short-duration measurements of typical wearable devices.
- *Comprehensive AF detection*: Capable of detecting both paroxysmal and persistent AF.
- *Multi-condition ECG acquisition*: Enables ECG monitoring under both resting and exercise conditions, supporting more realistic usage scenarios.
#h(2em)The system is implemented using an edge-based architecture to achieve real-time inference with low latency and enhanced data privacy.

== Comparison with Existing Solutions
#h(2em)Our system enables *long-term, continuous ECG monitoring*, representing a substantial advancement over typical commercial wearable devices that are generally restricted to short-duration recordings.

In addition, *the system incorporates cardiovascular risk assessment*, thereby enhancing the interpretability and clinical relevance of the acquired ECG signals.

Regarding AF detection, the proposed system is *capable of identifying both paroxysmal and persistent AF*, whereas many commercial devices primarily focus on heart rate monitoring or are limited to detecting persistent AF.

Furthermore, *the system is specifically designed for wearable, continuous operation and supports ECG acquisition under both resting and exercise conditions.* In contrast, many existing commercial devices rely on finger-contact measurements and are therefore limited to short-term, resting-state recordings.


#set text(size: 10pt)
#figure(
  table(
    columns: (auto, 1fr, 1fr),
    align: (left, left, left),
    stroke: 0.5pt,
    fill: (_, row) => if row == 0 { luma(230) } else { none },

    [*Comparison Metrics*], [*Proposed System*], [*Existing Wearable Devices*],

    [ECG Monitoring Duration], [Long-term continuous monitoring], [Short-duration recordings],

    [ECG Acquisition Conditions], [Resting and exercise ECG], [Primarily resting ECG],

    [Measurement Method], [Gel electrodes], [Dry electrodes \ (finger-contact required)],

    [Analytical Functionality], [ECG feature analysis, risk assessment, and AF detection], [Heart rate monitoring or limited AF detection],

    [AF Detection Capability], [Paroxysmal and persistent AF], [Persistent AF detection],

    [Computational Architecture], [Edge-based real-time inference with enhanced privacy], [Device-dependent; often limited on-device processing],
  ),
  caption: [Functional comparison with commercial products],
) <comparison>
#set text(size: 12pt)

== Potential Applications

#h(2em)For general users, the system provides interpretable insights into cardiovascular health status and potential risk factors, enabling timely preventive actions and early intervention. For healthcare professionals, it functions as an effective remote monitoring tool, supporting continuous observation of ECG signals and facilitating the prompt identification of clinically significant abnormalities or temporal changes.

Moreover, owing to its low-cost implementation and edge-based architecture, the system can be readily deployed across diverse settings, including community healthcare facilities and resource-constrained environments, thereby improving the accessibility and scalability of cardiovascular disease screening and management.

= Methodology and Implementation
== System Overview
//　　本作品硬體架構由 AD8232 ECG 感測模組、ESP32 與 Raspberry Pi 3B 組成。AD8232 負責單導程 ECG 訊號擷取，ESP32 負責資料取樣與傳輸，Raspberry Pi 3B 則負責訊號處理、特徵萃取、AF 偵測、風險推論與結果整合。此架構可在維持系統完整性的前提下兼顧成本、可攜性與邊緣部署需求。
#h(2em) The system consists of the following components: AD8232 ECG module, ESP32, and Raspberry Pi 3B. The AD8232 is responsible for single-lead ECG signal acquisition, while the ESP32 connects for data sampling and transmission, and the Raspberry Pi 3B receives those data for signal processing, feature extraction, AF detection, risk inference, and result integration. *This architecture can meet the cost, portability, and edge deployment requirements*, making it suitable for use in remote health monitoring applications where efficient and real-time ECG analysis is essential. @module_overview shows how these components interact within the overall system architecture and the services inside each module.

#figure(
  scale(70%, reflow: true)[#figures.module_overview],
  caption: [Module overview]
) <module_overview>

/*
　　而軟體流程的部分可分為四個主要模組：
+ 訊號處理：基於 Pan-Tompkins++ 演算法實作 R-peak 偵測，並加入 ST segment 相關分析 @imtiaz2024pan。
+ 特徵萃取：由 R-peak 計算 MaxHR、Oldpeak、ST_Slope、RestingECG 等特徵，提供風險評估模型預測。
+ AF 偵測：以 RR interval 為基礎，使用 RdR map 與 non-empty cell 計數進行判斷。
+ 風險評估：以 CatBoost 為核心，根據使用者輸入資料是否完整，自動切換模型進行預測。

#h(2em) The software pipeline could primarily be divided into four major modules:
+ Signal processing: R-peak detection based on Pan-Tompkins++ algorithm, followed by ST segment segmentation. @imtiaz2024pan
+ Feature extraction: Calculate MaxHR, Oldpeak, ST_Slope, and RestingECG features based on R-peak, followed by risk assessment model prediction.
+ AF detection: Determine AF episodes based on RR intervals using RdR map and non-empty cell count. 
+ Risk assessment: Utilize CatBoost as the main model, automatically switching between models based on user input data completeness.


#h(2em)The data pipeline is illustrated in @system_flow. The proposed system processes raw ECG signals through a sequence of signal processing, followed by two parallel modules for cardiovascular risk assessment and AF detection.

- Preprocessing:
#h(2em)The raw ECG signal is first preprocessed to enhance signal quality. This stage includes noise reduction, baseline wander removal to ensure robustness in subsequent analysis.

- R-peak Detection:
#h(2em)R-peaks are detected using the Pan-Tompkins++ algorithm @imtiaz2024pan, providing accurate localization of cardiac cycles. These detected peaks serve as the basis for both feature extraction and rhythm analysis.

- Feature Extraction:
#h(2em)Based on the detected R-peaks, features are extracted, including maximum heart rate (`MaxHR`), `Oldpeak`, `ST_Slope`, and Resting ECG indicators (`RestingECG`). These features are used for downstream cardiovascular risk evaluation.
- Parallel Analysis Modules
#h(2em)After R-peak detection, the pipeline branches into two parallel modules:

-- Risk Assessment Model:
#h(2em)The extracted features are input into a CVD risk assessment model to generate a risk score representing the likelihood of underlying cardiac conditions.

-- AF Detection:
#h(2em)Based on the RdR+NEC algorithm @lian2011af, our system constructs an RdR map by plotting consecutive RR intervals versus their beat-to-beat differences (dRR) to capture rhythm irregularity. Classifying AF by counting the number of non-empty cells (NEC) on a 25-ms resolution 2D grid over a 128-beat window.
*/

#list(
  [Preprocessing:\
  #h(2em)The raw ECG signal is first preprocessed to enhance signal quality. This stage includes noise reduction, baseline wander removal to ensure robustness in subsequent analysis.],
  [R-peak Detection:\ 
  #h(2em)R-peaks are detected using the Pan-Tompkins++ algorithm @imtiaz2024pan, providing accurate localization of cardiac cycles. These detected peaks serve as the basis for both feature extraction and rhythm analysis, as shown in @ecg_top_5.
  #figure(
    image("pics/ecg_top_mid5.png"),
    caption: [Illustration of R-peak detection on the ECG signal]
  ) <ecg_top_5>
  ],
  [Feature Extraction:\
  #h(2em)Based on the detected R-peaks, features are extracted, including maximum heart rate (`MaxHR`), `Oldpeak`, `ST_Slope`, and Resting ECG indicators (`RestingECG`). These features are used for downstream cardiovascular risk evaluation.],
  [Parallel Analysis Modules:\
  #h(2em)After R-peak detection, the pipeline branches into two parallel modules:\
  #list(
    marker: [#h(2em)--],
    [Risk Assessment Model:\
    #h(2em)The extracted features are input into a CVD risk assessment model to generate a risk score representing the likelihood of underlying cardiac conditions.],
    [AF Detection:\
    #h(2em)Based on the RdR+NEC algorithm @lian2011af, our system constructs an RdR map by plotting consecutive RR intervals versus their beat-to-beat differences (dRR) to capture rhythm irregularity. Classifying AF by counting the number of non-empty cells (NEC) on a 25-ms resolution 2D grid over a 128-beat window.]
  )
  ]
)


#figure(
  image("pics/data_flow.png"),
  caption: [Data flow of the system]
) <system_flow>

//在模型部署方面，本作品保留兩組 CatBoost 模型。8-feature 模型作為部署版本，適用於僅有基本資料與 ECG 特徵的情況；10-feature 模型則於使用者同時提供 Cholesterol 與 FastingBS 等額外健康資料時啟用，以獲得較高辨識效能。兩組模型大小約 650KB 等級，可於邊緣裝置進行推論。
/*
#h(2em) The two CatBoost models deployed in this study are retained. The 8-feature model is deployed for situations where only basic data and ECG features are available; the 10-feature model is enabled when users provide additional health data such as Cholesterol and FastingBS, resulting in higher accuracy.
The two models are approximately 650KB in size, and can be inferred on edge devices.
*/
== Cardiovascular Risk Prediction

=== Dataset and Problem Setup
#h(2em) We utilized cardiovascular disease datasets from the UCI repository, including the Cleveland, Hungary, Switzerland, and VA Long Beach databases, and further integrated them with the Stalog (Heart) dataset. After removing duplicate entries and records with missing values, the final dataset comprised 918 samples. It includes 11 input features and one target variable, as detailed in the following table.

#figure(
  table(
    columns: (auto, 1fr),
    align: (left, left),
    stroke: 0.5pt,
    fill: (_, row) => if row == 0 { luma(230) } else { none },

    [*Feature*], [*Description*],

    [Age], [Age of the patient (years)],
    [Sex], [Sex of the patient (M: Male, F: Female)],
    [ChestPainType], [Chest pain type (TA: Typical Angina, ATA: Atypical Angina, NAP: Non-Anginal Pain, ASY: Asymptomatic)],
    [RestingBP], [Resting blood pressure (mm Hg)],
    [Cholesterol], [Serum cholesterol (mm/dl)],
    [FastingBS], [Fasting blood sugar (1: >120 mg/dl, 0: otherwise)],
    [RestingECG], [Resting electrocardiogram results (Normal, ST: ST-T abnormality, LVH: left ventricular hypertrophy)],
    [MaxHR], [Maximum heart rate achieved (60–202)],
    [ExerciseAngina], [Exercise-induced angina (Y: Yes, N: No)],
    [Oldpeak], [ST depression value (numeric)],
    [ST_Slope], [Slope of peak exercise ST segment (Up, Flat, Down)],
    [HeartDisease], [Output class (1: Heart disease, 0: Normal)],
  ),
  caption: [Summary of Features for Heart Disease Dataset],
)<tab:features>

#h(2em) We conducted a feature ablation analysis to evaluate the contribution of each feature to the model’s predictive performance. Specifically, we compared the model accuracy when each feature was included versus excluded (See @feature_select). Therefore, we excluded this feature from the final deployed model (retaining 10 out of 11 features) to enhance robustness and generalization performance.
Additionally, since `Cholesterol` and `FastingBS` cannot be directly measured by our device and require user input, we designed a *dual-model system*. The 10-feature model is applied when all features are available, whereas an *8-feature model is used when `Cholesterol` and `FastingBS` are missing*. This design maintains strong predictive performance while ensuring reliable operation under incomplete data conditions.

#figure(
  image("pics/feature_select.png.webp", width: 80%),
  caption: [Ablation study on input features]
) <feature_select>

=== Preprocessing and Filters

#h(2em) Before extracting features, raw ECG signals must undergo noise filtering to ensure the accuracy of subsequent feature calculations.
Our project initially utilized a 5-12 Hz filter to process the QRS segment. However, this frequency band over-suppressed the T-wave, causing the false removal of genuine ST depression or ST elevation features.
To address this, we designed an *independent 0.5-35 Hz filtering interval specifically for the ST Slope calculation*, preserving complete and genuine ST segment features.

=== Feature Extraction Methods

#h(2em) Our processing pipeline primarily extracts four key features: Maximum Heart Rate, Oldpeak, ST Slope, and Resting Electrocardiogram (RestingECG). The R-peak measured by `Pan-Tompkins++` @imtiaz2024pan serves as the reference point for calculating all subsequent features (like heart rate and segment windows). The extraction mechanisms, challenges, and optimization processes are detailed below.

==== Maximum Heart Rate

#h(2em) *Definition*: The maximum heart rate achieved during the measurement period, typically yielding a numeric value between 60 and 202.

*Extraction Method*: By utilizing the `Pan-Tompkins++` algorithm, we were able to detect R-peaks, which are subsequently converted into the heart rate.

==== Oldpeak

#h(2em) *Definition*: Oldpeak represents the ST depression caused by activity in comparison to rest. A value > 0 may indicate angina, while a value < 0 is potentially related to myocardial infarction.
Oldpeak quantifies the absolute displacement of the ST segment relative to the electrically neutral PR baseline. In a healthy heart, the ST segment should be perfectly flush with the PR segment. When the heart muscle is stressed or deprived of oxygen (especially during the exercise phase of stress testing), the ST segment will deviate.

*Extraction Method*: It is calculated based on relative R-peak positions using the following formula:
$ "Oldpeak" = V_("ST level") - V_("PR baseline") $
#h(2em)Here, _PR baseline_ is the average potential between 200 ms and 120 ms prior to the R-peak, and _ST level_ is the average potential between 100 ms and 160 ms after the R-peak. 
This timing window is crucial for accurately measuring the ST segment's displacement, and is suggested by multiple medical literature sources. @hu2015morphological @zong2014real @campero2022interpretable

==== ST Slope

#h(2em) *Definition*: The slope of the peak exercise ST segment, classified into three categories: Up, Flat, or Down. While the Oldpeak measures the absolute drop or rise of the ST segment, the ST_Slope measures its morphological trajectory. How the ST segment behaves dynamically over time is a critical predictor of coronary artery disease.

*Algorithmic Execution*: Instead of taking a single average, the algorithm extracts all voltage data points within the defined ST Window and applies an Ordinary Least Squares linear regression to find the line of best fit:
$ V(t)=m t+b $
#h(2em)Here, t represents time, V(t) is the voltage, b is the y-intercept, and m is the computed slope.

*Diagnostic Classification*: We categorize the ST slope into three categories: Up (upsloping), Flat, or Down (downsloping). 
- _Upsloping_: $m > 0.5 V/s$. (Often seen in normal, healthy exercise responses, even if slight ST depression is present).
- _Downsloping_: $m < −0.5 V/s$. (A highly specific indicator of severe ischemic heart disease).
- _Flat_: $abs(m) <=0.5 V/s$. (Also a strong indicator of ischemia, as a healthy ST segment should naturally slope upward into the T-wave).

==== Resting Electrocardiogram (RestingECG)

#h(2em) *Definition*: RestingECG is categorized into Normal, ST (having ST-T wave abnormality, such as T-wave inversion or ST elevation/depression > 0.05 mV), and LVH (showing probable or definite left ventricular hypertrophy by Estes' criteria).

*T-wave Difficulties*: T-waves are low-frequency, low-amplitude signals that are highly susceptible to baseline wandering, which is a type of low-frequency noise primarily caused by the user's respiration and minor electrode movements.

*Solution*: 
+ Initial Attempt: To stabilize the T-wave for accurate inversion detection, we integrated a Wavelet Transform-based Baseline Wandering Removal algorithm (utilizing the open-source py-bwr library).
+ The Trade-off: While BWR successfully clarified the T-wave inversion morphology, testing revealed a critical flaw: the mathematical transformation aggressively warped the raw voltage levels, severely degrading the accuracy of ST elevation/depression measurements. Overall model accuracy dropped from 92.39% without BWR to 83.42% with global BWR.
+ Final Pipeline: To resolve this, the system employs a *bifurcated processing strategy*. Baseline correction is applied only in parallel streams specifically evaluating T-wave morphology, while *the original minimally filtered signal (0.5–35 Hz) is strictly preserved for calculating absolute ST segment offsets*.

#figure(
  image("pics/TWave.png"),
  caption: [The bifurcated processing strategy for T-wave morphology correction.],
) 

#h(2em) *LVH Difficulties*: And for LVH, since it requires precordial leads—specifically V1, V5, and V6, we implemented a practical software-based workaround. During the initial profile registration on our web interface, the system proactively prompts users to input their known medical history, including any prior LVH diagnoses. This approach ensures that the machine learning model still receives the complete data array required for a comprehensive risk assessment.

==== Validation: 
#h(2em) We validated the accuracy of the STE/STD feature by comparing it with the European ST-T Database. *The accuracy of recognizing ST Elevation/Depression was found to be 99.16% and recall of ST Elevation/Depression was 91.6%.*

#figure(
  image("pics/ST_CM.png", width: 70%),
  caption: [Confusion matrix for ST Elevation/Depression recognition.],
)

// Maybe also plot with annotations
#figure(
  image("pics/Plot_with_annotations.png"),
  caption: [Plots of ECG signal with features annotated.],
)

=== Model Training Methodology and Techniques

#h(2em) The final deployed 10-feature CatBoost model achieved *96.57% accuracy and 97.06% recall* on the holdout test set after fine-tuning and threshold tuning, demonstrating that ECG-derived features can be translated into reliable cardiovascular risk predictions.

==== Feature Preprocessing
#h(2em)First, public heart disease datasets were reconstructed into a comprehensive labeled dataset (918 records) with standardized feature naming and data types. Categorical variables were transformed into numerical representations via label encoding, while missing numerical values were handled using mean imputation to prevent training bias resulting from data omissions. 
To address the issue of class imbalance, oversampling was employed during the training phase. This approach ensures a more balanced distribution of positive and negative classes, thereby enhancing the model's ability to identify minority classes.
==== Training
#h(2em)Regarding data partitioning, this study adopted an 80/20 holdout split (80% training set; 20% test set) consistent with existing literature, performing cross-validation and hyperparameter optimization within the training set. A progressive evolution strategy was applied to model development; initially, multiple baseline models were evaluated, including Logistic Regression, Gradient Boosting, CatBoost, and an average probability Ensemble model. Through comprehensive comparison, CatBoost exhibited the highest potential. 
Consequently, the final deployed model in this study evolved directly from the CatBoost baseline. By performing further fine-tuning, we effectively improved the consistency between offline evaluation and deployment behavior. The final deployed CatBoost model converged with the following hyperparameters: (iterations=600, learning_rate=0.1, depth=6, l2_leaf_reg=3, random_seed=42).

#figure(
  image("pics/model_training.png"),
  caption: [Flowchart of Model Development and Training],
) <model_training>

==== Classification
#h(2em)To balance prediction accuracy and system robustness, a *Dual-model Routing mechanism* was designed for the inference stage. When a user provides a complete set of clinical features, the system prioritizes the 10-Feature Model to deliver the best predictive performance. Conversely, if specific fields are missing, the system automatically switches to the 8-Feature Model, which utilizes data directly captured by our device's sensors to ensure stable and continuous output even under conditions of incomplete information.


== AF Detection Methodology and Validation

#h(2em)During the early development of the AF detection module, the Coefficient of Variation (CV) test method was initially employed @tateno2001automatic. While this method is fast to implement and computationally efficient, its decision criteria are fundamentally based on a single statistic. This makes it prone to misidentifying ectopic rhythms, such as Premature Ventricular Contractions (PVCs), as AF, leading to a high false alarm rate in practical applications.

To address this issue, a multi-feature integration approach proposed by Dash et al @dash2009automatic. This academic article was subsequently explored, which utilizes TPR, RMSSD, and Shannon Entropy (SE) to improve discriminatory power. As shown in the comparative results, this integrated approach achieved excellent classification results on the AFDB dataset. However, this method involves complex feature extraction and precise parameter tuning, incurring high engineering overhead and significantly longer computation times.

After a comprehensive evaluation of classification performance, false alarm control, algorithmic complexity, and maintenance costs, the RdR+NEC method @lian2011af was ultimately selected for this work. This method offers the dual advantages of simple decision rules and *extremely low computational complexity*.

In the deployed system, *the final RdR+NEC version achieves 95.73% accuracy, 95.72% sensitivity, 95.74% specificity, and 1.167 ms/window* while satisfying the requirements for real-time execution on edge devices.

The specific technical details and parameter settings of the RdR+NEC algorithm are as follows:

=== RdR Map Construction
#h(2em) Unlike the traditional Lorenz plot which utilizes a single dimension, this method maps successive RR intervals ($"RR"_i$) and their differences ($"dRR"_i = "RR"_i - "RR"_(i-1)$) simultaneously onto a two-dimensional coordinate system. This design captures both heart rate and heart rate variability (HRV) information. During AF episodes, irregular rhythms cause data points to scatter randomly across a wide area of the map; conversely, normal or regular rhythms typically present as dense, localized clusters.

=== Gridding and Non-empty Cells (NEC)
#h(2em) The system divides the RdR map into a two-dimensional grid. For each input segment containing 128 cardiac cycles (128-beat window), the number of Non-empty Cells (NEC) is calculated. This count quantifies the degree of dispersion to classify the rhythm as AF or non-AF.

=== Threshold Determination
#h(2em) Based on the optimization analysis in @lian2011af, an NEC threshold of 65 was determined to provide optimal performance for a 128-beat window configuration.

=== Edge Deployment Advantages
#h(2em) Compared to methods requiring extensive feature extraction or complex floating-point operations, *RdR+NEC relies solely on a single integer count of NECs for classification*. Its low computational overhead enables high-precision monitoring while satisfying the real-time and long-term monitoring requirements of battery-powered wearable devices.

#figure(
  image("pics/af_detect.png"),
  caption: [An example of Atrial Fibrillation (AF) Detection],
) <af_detect>

#h(2em) To confirm the algorithm's generalization capabilities, verification was conducted across multiple public datasets. As indicated in Table 3, the RdR+NEC method demonstrates highly stable and superior detection performance across diverse data distributions.

#text(size: 10pt)[Table 5. Performance validation results of the RdR+NEC method across public datasets]


#figure(
  table(
  columns: (2fr, 1fr, 1fr),
  align: (left, center, center),
  stroke: 0.5pt,
  fill: (_, y) => if y == 0 { luma(230) } else { none },
  [*Database*], [*Sensitivity*], [*Specificity*],

  [NSRDB], [NA\*], [88.10],
  [NSR2DB], [NA\*], [96.30],
  [AFDB], [95.70], [95.70],
  [Combined database], [95.70], [94.20],
),
  caption: [Hardware Cost Breakdown of the Proposed System],
)<tab:AF_compare>

\* #text(size: 10pt)[NA: Sensitivity is not applicable because no true AF episodes are present.]

== TAIDE-based health assistant

#h(2em) To enhance user experience and provide personalized health insights, we integrated an advanced AI assistant directly into the frontend interface. 

For the core language model, we selected *Gemma-3-TAIDE-12b-Chat*, a robust 12-billion parameter model optimized by the TAIDE project. This specific model was chosen for its excellent reasoning capabilities and its strong proficiency in handling Traditional Chinese, ensuring that the health advice and explanations provided to users are both accurate and natural to read.

Due to the substantial computational requirements of running a 12B parameter model, we *deployed the language model as a dedicated server hosted on a Spark DGX system*. This backend server handles all the heavy AI inference tasks. When a user requests health insights on the frontend application, the system makes a call to the server, retrieving the AI-generated responses efficiently. *This client-server architecture ensures that the frontend remains highly responsive and accessible*, without being burdened by the intensive processing demands of the large language model.


#figure(
  [
    ```python
    system = (
          "你是健康助理。根據使用者的心臟健康指標，提供簡短、具體、非診斷性的建議。"
          "避免宣稱確診；若有危急徵象請提醒就醫。使用繁體中文。"
          "輸出請以 2~3 點條列為主，最後加一句提醒此為一般建議非醫療診斷。"
          "輸出格式為純文字，不使用任何styling。"
      )
    ```
  ],
  caption: [TAIDE-based health assistant system prompt],
  kind: "Code",
  supplement: [Snippet],
)
#figure(
  image("pics/taide_example.png"),
  caption: [TAIDE-based health assistant response],
)

== System Deployment, Cost Analysis, and Feasibility
#h(2em)To evaluate the practical feasibility of the proposed system, we analyze the hardware cost structure and deployment requirements.

The system consists of the following key components:
#figure(
  table(
    columns: (2.5fr, 3.5fr, 1.5fr),
    align: (left, left, right),
    stroke: 0.5pt,
    fill: (_, y) => if y == 0 { luma(230) } else { none },

    [*Component*], [*Function*], [*Cost (TWD)*],

    [AD8232 ECG module], [ECG signal acquisition], [\~200],
    [ESP32], [Data acquisition and transmission], [\~150],
    [Raspberry Pi 3B], [Edge processing], [\~1,500],
    [Power module & peripherals], [Battery and supporting components], [\~100],
    [*Total*], [], [*< 2,000*],
  ),
  caption: [Hardware Cost Breakdown of the Proposed System],
)<tab:cost>

#h(2em)*The total system cost is maintained below 2000 TWD*, which is significantly lower than most commercial wearable ECG devices.
From a system perspective, the proposed design achieves a favorable trade-off between computational capability, model complexity, and deployment cost. The use of lightweight machine learning models (approximately 650 KB) enables real-time inference on edge devices without requiring specialized hardware acceleration.
Compared to smartwatch-based ECG systems, which typically rely on proprietary hardware ecosystems and external processing pipelines, the proposed system provides a transparent and cost-efficient architecture with full control over signal processing and inference.
These results indicate that the proposed system is both technically effective and economically viable for large-scale deployment in home healthcare and remote monitoring scenarios.

== Prototype Implementation and System Demonstration
#figure(
  image("pics/wearing_config.png", width: 70%),
  caption: [Wearable ECG System Configuration and Electrode Placement],
) <wearing_config>
#figure(
  image("pics/hardware.png", width: 40%),
  caption: [Hardware Implementation of the Wearable ECG Monitoring System],
) <hardware>

#figure(
  image("pics/frontend.png"),
  caption: [Frontend interface]
) <frontend>
/*
= 技術限制、風險與可信度說明
　　為提高作品可信度，本作品亦主動說明現階段限制如下：
+ 目前主要使用單導程 ECG，與醫療級多導程系統相比，資訊量仍有限。
+ 心臟疾病風險評估模型主要基於公開資料集驗證，未來仍需更多真實使用場景驗證。
+ 心房顫動 (AF) 偵測目前以公開資料庫與原型資料進行驗證，未來仍可補充更大規模使用者測試。
+ LLM 健康建議若作為後續功能，僅應視為輔助性資訊，不應取代醫師診斷。
+ 本系統定位為健康管理與早期警示工具，而非醫療診斷設備。
*/

= Research Outcomes and Benefits
== Enhancement of Early Detection Capability of Cardiovascular Abnormalities
#h(2em)The proposed system significantly enhances the early detection capability of cardiovascular abnormalities by enabling continuous, long-term ECG monitoring.

Conventional wearable ECG systems are typically limited to short-duration or user-triggered recordings, which may fail to capture transient or intermittent cardiac events, such as paroxysmal AF. This limitation reduces the likelihood of early-stage detection, particularly for conditions that exhibit irregular temporal patterns.

In contrast, the proposed system supports continuous ECG acquisition and incorporates a rhythm analysis mechanism based on RR interval dynamics. By utilizing the RdR + NEC method, the system is able to effectively characterize irregular heartbeat patterns over extended time windows.

The ESP32 samples ECG continuously and transmits the data through a Wi-Fi link to the Raspberry Pi, where preprocessing and AF detection run in parallel with live visualization. The backend then streams ECG frames to the frontend through WebSocket, allowing users to observe real-time waveforms while the system analyzes rhythm irregularity.

The selected RdR+NEC demonstrates that the edge-based pipeline can balance early warning performance with low computational overhead. This design improves the likelihood of detecting subtle or sporadic abnormalities that would otherwise be missed in short-term measurements, and it provides a reliable foundation for preventive cardiovascular monitoring.

#set text(size:11pt)
#figure(
  table(
    columns: (2.5fr, 1fr, 1fr, 1fr, 1.8fr),
    align: (left, center, center, center, center),
    stroke: 0.5pt,
    fill: (_, y) => if y == 0 { luma(230) } else { none },
    [*Method*], [*Sensitivity*], [*Specificity*], [*Accuracy*], [#par(justify: false)[*Computation time*]],

    [CV test], [90.91], [77.67], [78.62], [0.294 ms/window],
    [RMSSD+TPR+SE], [98.99], [87.12], [87.97], [10.107 ms/window],
    [RdR+NEC (selected method)], [95.72], [95.74], [95.73], [1.167 ms/window],
  ),
  caption: [AF detection method comparison on the MIT-BIH dataset],
) <tab:af_method_results>
== From Raw ECG Signals to Interpretable Risk Representation
#h(2em)We introduce a unified feature extraction framework and a feature-based predictive model that map raw ECG signals to clinically relevant indicators for cardiovascular disease assessment. This representation enables the model to operate in a semantically meaningful feature space, rather than directly on high-dimensional raw signals. Furthermore, the feature-based approach reduces computational complexity, resulting in low overhead and enabling real-time execution on edge devices.

The final deployed 10-feature CatBoost model achieved 96.57% accuracy and 97.06% recall on the holdout test set after fine-tuning and threshold tuning, and the precision, F1-score, and ROC-AUC are also showing that the extracted ECG features are sufficient for an interpretable and accurate risk model. Results on the holdout test set clearly illustrate the model's evolution trajectory: starting from the initial CatBoost baseline model (accuracy 85.87%, recall 85.29%), moving through fine-tuning, and culminating in threshold tuning.

#set text(size:8pt)
#figure(
  table(
    columns: (2.7fr, 4.3fr, 1fr, 1fr, 1fr, 1fr, 1fr),
    align: (left, left, center, center, center, center, center),
    stroke: 0.5pt,
    fill: (_, y) => if y == 0 { luma(230) } else { none },
    [*Model*], [*Parameter*], [*Accuracy*], [*AUC*], [*Precision*], [*Recall*], [*F1*],

    [CatBoost], [{verbose=False, random_state=369}], [85.87], [90.35], [88.78], [85.29], [87.00],
    [LogisticRegression], [{max_iter=5000, random_state=369}], [87.50], [92.53], [89.11], [88.24], [88.67],
    [GradientBoosting], [{random_state=369}], [85.33], [91.69], [90.32], [82.35], [86.15],
    [Ensemble], [ ], [86.96], [92.06], [90.62], [85.29], [87.88],
    [CatBoost after fine-tuning (before threshold tuning)], [(iterations=600, learning_rate=0.1, depth=6, l2_leaf_reg=3, random_seed=42)], [91.67], [88.08], [95.70], [87.25], [91.28],
    [CatBoost after fine-tuning (after threshold tuning)], [(iterations=600, learning_rate=0.1, depth=6, l2_leaf_reg=3, random_seed=42, threshold=0.20)], [96.57], [97.67], [96.12], [97.06], [96.59],
  ),
  caption: [Comparison of model performance metrics on the holdout test set],
) <tab:cvd_training_results>

#set text(size:12pt)
#figure(
  image("pics/roc_comparison_single_chart.png", width: 75%),
  caption: [ROC curve comparison on test set],
) <roc_compare>

== Lightweight Edge Backend Deployment

#h(2em)To evaluate deployment feasibility on resource-constrained hardware, we profiled the backend service on Raspberry Pi 3B under a representative user workflow. The device was first allowed to warm up at room temperature, and the Dockerized backend service was then launched at 19:30 after thermal stabilization. Five minutes later (19:35), interactive testing began with sequential operations including user login, health-data upload, chart inspection, live ECG viewing, and risk assessment.

As shown in @device_temprature and @cpu_usage, the backend maintained a consistently low computational footprint during routine operation. CPU utilization remained below 10% for most of the session, with only short transient increases during ECG chart rendering and risk-inference execution. Thermal behavior was similarly stable: the Raspberry Pi temperature was maintained around 54℃ throughout testing, corresponding to an increase of only approximately 4℃ compared with the idle baseline.

These results indicate that the proposed backend service is sufficiently lightweight for sustained edge deployment. The system supports real-time interaction and model inference while preserving stable thermal and computational conditions, demonstrating practical suitability for long-term home and community healthcare scenarios.

#figure(
  image("pics/device_temperature.png"),
  caption: [Raspberry Pi 3B's temperature over time]
) <device_temprature>

#figure(
  image("pics/docker_cpu_usage.png"),
  caption: [CPU usage of the service in Docker]
) <cpu_usage>

= Conclusion and Future Work
== Conclusion
#h(2em)Our project presents a *highly integrated, low-cost, and edge-based wearable ECG monitoring system* designed to bridge the gap between expensive clinical diagnostics and limited commercial smartwatches. By combining an AD8232 sensor, an ESP32 microcontroller, and a Raspberry Pi 3B, we established a robust hardware architecture *capable of long-term, continuous cardiovascular monitoring under both resting and exercise conditions*. 

Algorithmically, the system successfully translates raw ECG signals into interpretable clinical indicators. The implementation of a *dual-model CatBoost routing mechanism ensures robust cardiovascular disease risk prediction (achieving up to 96.57% accuracy)* even with incomplete user data. Concurrently, the integration of the computationally efficient RdR+NEC algorithm *enables the real-time detection of both paroxysmal and persistent atrial fibrillation* with minimal computational overhead on edge devices. Complemented by a *TAIDE-based large language model*, the system empowers users with personalized and intuitive health insights. Overall, this framework offers an accessible, scalable, and privacy-preserving solution for proactive cardiovascular screening in home healthcare settings.

== Future work
#h(2em)However, our proposed system still has its limitations: our system still only supports single-lead ECG and might not be representative enough for cardiovascular disease (We've planned to *expand to multi-lead ECG* in the future to increase the amount of information for risk assessment). Also, our system still relies on gel-electrode contact for ECG measurement.

The system can be further extended to support multi-lead ECG acquisition, thereby enriching the information available for cardiovascular risk assessment. In addition, the current wired configuration and reliance on gel-based electrodes may limit user comfort and usability. Future work may therefore *investigate wireless electrode designs or dry electrode technologies* to enhance wearability and support long-term use. Furthermore, the system could be *integrated with cloud-based services to enable home-based diagnosis and remote monitoring*, allowing users to share ECG data and risk assessment results with healthcare professionals for more comprehensive and continuous care.

#bibliography(
  "works.bib",
  style: "ieee",
  title: [6 References],
)
