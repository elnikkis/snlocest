# ネットワークベース位置推定ライブラリ locest

snlocestは [Hironaka 16], [廣中 17] で使われたネットワークベースの居住地推定手法の実装です。

Twitterの位置情報付きツイートとフォローデータを使ってソーシャルネットワーク＋ユーザ（ノード）の位置データ作成をするスクリプトと、ソーシャルネットワーク＋ノードの位置データを使ってノードの位置を推定をして性能を評価するスクリプトが含まれています。

- [Hironaka 16] Hironaka, S., Yoshida, M., Umemura, K. “Analysis of Home Location Estimation with Iteration on Twitter Following Relationship”. 2016 International Conference On Advanced Informatics: Concepts, Theory And Application. 2016, pp. 1--5.
- [廣中 17] 廣中詩織, 吉田光男, 岡部正幸, 梅村恭司. 日本における居住地推定に利用するためのフォロー関係の調査. 人工知能学会論文誌. 2017, vol. 32, no. 1, pp. WII-M\_1--11.


## 実行環境

 + Python 3.5 以上（subprocess.runを使っている）
 + Miniconda
 + numpy, scipy, pandas, scikit-learn, shapely, など

実際の実行環境の情報は `conda_env.yaml` にあります。
次のコマンドで作成しました。

```
$ conda env export > conda_env.yaml
```

この情報をもとに、次のコマンドで同等の環境が作成できます。

```
$ conda env create --file conda_env.yaml
$ pip install .
```


### 実際の環境構築に利用したコマンド

```
conda create -n locest35 python=3.5
conda install ipython numpy scipy matplotlib scikit-learn jupyter pandas
conda install shapely networkx pytest
conda install -c conda-forge rtree
pip install luigi
pip install geopy
pip install csvkit
pip install -e .
```


## 使い方

注意: パス中にスペースを含むと動作しないスクリプトがたくさん含まれています

### ディレクトリ構成

Twitterの位置情報付きツイート、Twitterユーザ間のフォローデータが必要である。
これらのほかに、緯度経度からその座標を含む市区町村を照合するためにG-XMLデータが必要である（公開予定）。

位置情報付きツイート、フォローデータは、次のディレクトリに保存されているとする。

- `data/twitter-geo/japan/YYYY-MM/json_YYYY-MM-DD.txt.gz` 位置情報付きツイート
- `data/twitter-following-followers-geo/YYYYMM-{following,followers}.tar.gz` 以下のフォローデータのtar.gz圧縮
    - `YYYY-MM/YYYY-MM-\*.txt` APIから取得した `friends/ids` と `followers/ids` の関係データ（関係元と関係先のセミコロン区切り）
    - `YYYY-MM/unknown.txt` フォロー関係が取得できなかったuser idのリスト
- `data/areadata/japan-gxml.tsv.gz` エリアデータ

- `data/areadata/area_database.tsv` エリアのメタデータ
- `data/geotweets/` 位置情報付きツイートの処理中のデータが出力されるディレクトリ
- `data/datasets/` 作成したデータセットが出力されるディレクトリ

- `data/experiments/` 推定結果、評価結果が出力されるディレクトリ


### データセット作成

次のコマンドで、 2014年1月1日から2014年12月31日のあいだの位置情報付きツイートをもとに、ユーザの居住地データ（`data/geotweets/homelocation/majority/*.tsv`）を出力する。

```
$ luigi --module snlocest.tools.geotweet --local-scheduler SelectMajorityHomeLocation --date-range 2014-01-01-2015-01-01 --min-majoritynum 5
```

次のコマンドで、ユーザの居住地データと2015年7月に取得したフォローデータをもとに、ソーシャルネットワークとユーザの位置データを含むデータセットを `data/datasets/follow-201507_2014/` へ出力する。

```
$ luigi --local-scheduler --module snlocest.tools.socialnetwork FollowSocialNetworks --RemainedHomeLocation-homelocation-path data/geotweets/homelocation/majority/2014-01-01-2015-01-01_MinMajorityNum-5_MinTotalNum-1.tsv --name follow-201507_2014 --month 2015-07
```


### 居住地推定

次のコマンドで、Leave-one-out交差検証、10分割交差検証で、4つの居住地推定手法、4つのユーザ間の関係をもとにしたソーシャルネットワークを組み合わせたときの性能評価をする。

```
luigi --local-scheduler --module snlocest.tools.experiment KFoldEvaluation --name closed_follow-201507_2014
luigi --local-scheduler --module snlocest.tools.experiment LeaveOneOutEvaluation --name closed_follow-201507_2014
```
