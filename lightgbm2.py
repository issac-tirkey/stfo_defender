import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import train_test_split

df = pd.read_csv('your_flow_data.csv')

features = df[['tnfe', 'cp_median', 'apit_iqr', 'apit_std', 'apit_mean', 'apit_cv', 'apit_skewness', 'apit_kurtosis']]
labels = df['Label']

X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2, random_state=42)

train_data = lgb.Dataset(X_train, label=y_train)
test_data = lgb.Dataset(X_test, label=y_test)

params = {
    'boosting_type': 'gbdt',
    'objective': 'binary',
    'metric': 'binary_logloss',
    'learning_rate': 0.12,
    'num_leaves': 30,
    'max_depth': 6
}

model = lgb.train(
    params=params,
    train_set=train_data,
    num_boost_round=300,
    valid_sets=[test_data],
    callbacks=[
        lgb.early_stopping(stopping_rounds=50),
    ]
)

model.save_model('mitigation_model.txt')
