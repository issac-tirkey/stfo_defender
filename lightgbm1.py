import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Load and preprocess your dataset
# Assuming `X` is your feature matrix and `y` is a vector of labels
X, y = load_dataset()

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize LightGBM dataset structure
train_data = lgb.Dataset(X_train, label=y_train)
test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)

# Set up the parameters for LightGBM
params = {
    'objective': 'binary',  # for binary classification
    'metric': 'binary_logloss',
    'boosting_type': 'gbdt',
    'learning_rate': 0.12,
    'num_leaves': 30,
    'max_depth': 6,
    'min_data_in_leaf': 20,
    'bagging_fraction': 0.8,
    'feature_fraction': 0.8,
    'bagging_freq': 5,
}

# Train the model
gbm_model = lgb.train(
    params=params,
    train_set=train_data,
    num_boost_round=300,
    valid_sets=[test_data],
    early_stopping_rounds=50
)

# Save the model
gbm_model.save_model('lightgbm_model.txt')

# Make predictions
y_pred = gbm_model.predict(X_test, num_iteration=gbm_model.best_iteration)
# Convert probabilities into binary output
y_pred_binary = [1 if prob > 0.5 else 0 for prob in y_pred]
# Evaluate the model
accuracy = accuracy_score(y_test, y_pred_binary)
print(f'Model accuracy: {accuracy}')
