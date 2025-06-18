The dynamic and phase character of T20 cricket makes it difficult to figure it out bowler 
performance and effective matchup roles. The traditional approaches lack context-specific 
data that are needed in match planning, particularly between different phases like Powerplay, 
Middle Overs, and Death Overs. Coaches and analysts require frameworks to intelligently 
interpret past performance and suggest suitable bowler roles with transparency and data
driven support. 
This research introduces a bowler matchup prediction system that applies machine learning 
techniques to analyze bowler performance based on match phase based Key Performance 
Indicators (KPIs) such as dot ball percentage, economy rate, and bowling average. Initially, 
unsupervised clustering methods like DBSCAN and GMM were explored, but K-Medoids 
was ultimately selected for its better performances. For predictive modelling, both Random 
Forest and Gradient Boosting classifiers were used to estimate bowler roles and evaluate 
feature importance. The project leverages the Deep Player Performance Index (DPPI)—a pre
existing role-based player evaluation metric—to support the analysis. 
Evaluation of the system was conducted using data science metrics. Clustering performance 
was validated using Silhouette Score, Davies-Bouldin Index and Calinski-Harabasz Index to 
ensure meaningful bowler roles segmentation. Predictive accuracy was assessed through 
Precision, Recall, F1 Score, and Accuracy metrics for both Random Forest and Gradient 
Boosting models. Feature importance outputs helped validate the influence of KPIs on role 
predictions. The results demonstrate the system’s ability to provide insightful, interpretable, 
and phase-specific role predictions for T20 cricket bowlers.  
