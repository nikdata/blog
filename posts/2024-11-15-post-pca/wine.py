import polars as pl
import polars.selectors as cs
import numpy as np
import seaborn as sns
import seaborn.objects as so
import matplotlib.pyplot as plt
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

# from matplotlib.font_manager import get_font_names
# print(get_font_names())

#  adjust the output to console width
pl.Config.set_tbl_rows(30)
pl.Config.set_tbl_width_chars(1000)
pl.Config.set_tbl_cols(-1)

raw_wine = pl.read_csv('wine-data.csv')

raw_wine.head()

# replace spaces
df_wine = raw_wine
df_wine.columns = [x.lower().replace(' ','_') for x in raw_wine.columns]

df_wine.head()

# multicollinearity
df_vif = pl.DataFrame({'variable': df_wine.select(pl.exclude('id','quality')).columns}).with_columns(vif = pl.Series([variance_inflation_factor(df_wine.select(pl.exclude('id','quality')).to_numpy(), i) for i in range(df_wine.shape[1]-2)])).sort(by = ['vif'], descending = True)

df_vif

# check for outliers
df_wine.describe(percentiles=[0.25, 0.5, 0.75, 0.90, 0.95, 0.99])

sns.set_theme(font = 'DejaVu Sans')
sns.set_style('ticks')
plt.style.use('dark_background')
fig, ax = plt.subplots(1,1,figsize = (8,4))
ax = sns.boxplot(x = df_wine.select('total_sulfur_dioxide').to_numpy().ravel(), color=(110/255,110/255,110/255), fill='steelblue', ax = ax, flierprops={'markerfacecolor': 'steelblue', 'markeredgecolor':'steelblue'})
ax.set_xlabel('Total Sulfur Dioxide')
ax.set_title('Boxplot: Total Sulfur Dioxide')
sns.despine(top = True, left=True, right=True)
fig.tight_layout()
plt.show()

# notice the outliers
sns.set_theme(font = 'DejaVu Sans')
sns.set_style('ticks')
plt.style.use('dark_background')
fig, ax = plt.subplots(1,1,figsize = (8,6))
ax = sns.boxplot(x = df_wine.select('quality').to_numpy().ravel(), y = df_wine.select('total_sulfur_dioxide').to_numpy().ravel(), color=(110/255,110/255,110/255), fill='steelblue', ax = ax, flierprops={'markerfacecolor': 'steelblue', 'markeredgecolor':'steelblue'})
ax.set_xlabel('Quality Rating')
ax.set_ylabel('Total Sulfur Dioxide')
sns.despine(top = True, left=True, right=True)
plt.yticks(np.arange(0,320, 20))
fig.tight_layout()
plt.show()



# class split
df_wine.group_by('quality').len().sort(by = 'quality', descending = False)

# find correlations
df_cor = df_wine.select(pl.exclude('id','quality')).corr()
cln_cor = df_cor.with_columns(var2 = pl.Series(df_cor.columns)) \
        .unpivot(index = 'var2', value_name='correlation') \
        .filter(pl.col('variable') != pl.col('var2')) \
        .with_columns(pl.concat_str(['variable','var2'], separator = ',').str.split(',').list.eval(pl.element().sort()).alias('sorted_pair')) \
        .with_columns(rownum = pl.col('sorted_pair').cum_count().over('sorted_pair')) \
        .filter(pl.col('rownum') == 1) \
        .select(pl.exclude('sorted_pair','rownum')) \
        .with_columns(abs_corr = pl.col('correlation').abs()) \
        .sort(by = 'abs_corr', descending = True) \
        .select(pl.exclude('abs_corr'))

# create a new response variable to analyze quality in 2 levels: low & high
cln_wine = df_wine.with_columns(high_quality = pl.when(pl.col('quality') <= 5).then(pl.lit(0)).otherwise(pl.lit(1)))

cln_wine.group_by('high_quality').len()

# df_wine: raw quality
# cln_wine: grouped quality

# columns
preds = df_wine.select(pl.exclude('id','quality'))
resp = df_wine.select('quality')

# train test split
xtrain, xtest, ytrain, ytest = train_test_split(preds, resp, test_size=0.3, stratify=resp,  random_state=1337)

xtrain.columns
xtest.columns

# standardize data
scaler = StandardScaler()

# fit on training data
scaler.fit(xtrain)

# apply to train & test
xtrain_scaled = scaler.transform(xtrain)
xtest_scaled = scaler.transform(xtest)

# convert back to dataframe
xtrain_scaled = pl.from_numpy(xtrain_scaled, schema = xtrain.columns)
xtest_scaled = pl.from_numpy(xtest_scaled, schema = xtest.columns)

len(xtrain.columns)

# define PCA model
pca = PCA(n_components=len(xtrain.columns))

# fit pca to training dataset
pca_train = pca.fit_transform(xtrain_scaled)
pca_test = pca.fit_transform(xtest_scaled)

# make a pretty version of explained ratio

df_pca = pl.DataFrame({'components': np.arange(0,11)+1,'explained_variance': pca.explained_variance_ratio_}).with_columns(pl.col('explained_variance').cum_sum().alias('cumulative_variance'))

df_pca

# seems like 5 components answer 80% of the variance
# 80% is just a good number;

logmdl = LogisticRegression(solver='liblinear')
logmdl.fit(xtrain_scaled, ytrain)

ypred = logmdl.predict(xtest)

accuracy_score(ytest, ypred)


logmdl_pca = LogisticRegression(solver='liblinear')
logmdl_pca.fit(pca_train, ytrain)
ypred_pca = logmdl_pca.predict(pca_test)

accuracy_score(ytest, ypred_pca)





# we have imbalance, so let's reclassify and see if we can improve accuracy
# columns
preds = cln_wine.select(pl.exclude('id','quality', 'high_quality'))
resp = cln_wine.select('high_quality')

# train test split
xtrain, xtest, ytrain, ytest = train_test_split(preds, resp, test_size=0.3, stratify=resp,  random_state=1337)

# standardize data
scaler = StandardScaler()

# fit on training data
scaler.fit(xtrain)

# apply to train & test
xtrain_scaled = scaler.transform(xtrain)
xtest_scaled = scaler.transform(xtest)

# convert back to dataframe
xtrain_scaled = pl.from_numpy(xtrain_scaled, schema = xtrain.columns)
xtest_scaled = pl.from_numpy(xtest_scaled, schema = xtest.columns)

# define PCA model
pca = PCA(n_components=len(xtrain.columns))

# fit pca to training dataset
pca_train = pca.fit_transform(xtrain_scaled)
pca_test = pca.fit_transform(xtest_scaled)

# make a pretty version of explained ratio

df_pca = pl.DataFrame({'components': np.arange(0,11)+1,'explained_variance': pca.explained_variance_ratio_}).with_columns(pl.col('explained_variance').cum_sum().alias('cumulative_variance'))

df_pca

# seems like 5 components answer 80% of the variance
# 80% is just a good number;

logmdl = LogisticRegression(solver='liblinear')
logmdl.fit(xtrain_scaled, ytrain)

ypred = logmdl.predict(xtest)

accuracy_score(ytest, ypred)


logmdl_pca = LogisticRegression(solver='liblinear')
logmdl_pca.fit(pca_train, ytrain)
ypred_pca = logmdl_pca.predict(pca_test)

accuracy_score(ytest, ypred_pca)