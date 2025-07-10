# CSV文件结构说明

基于`_format_result`函数的分析，各个CSV文件的正确结构如下：

## 📊 文件结构总览

### 1. **w权重系数** (`w_coefficients.csv`)
```
           turbidity    ss      sd      do     ...
STZ1       0.123       0.456   0.789   1.012  ...
STZ2       0.234       0.567   0.890   1.123  ...
STZ3       0.345       0.678   0.901   1.234  ...
...
STZ25      0.987       0.654   0.321   0.098  ...
```
- **行索引**: 特征编号 (STZ1, STZ2, ..., STZ25)
- **列索引**: 水质参数 (turbidity, ss, sd, do, codmn, codcr, chla, tn, tp, chroma, nh3n)
- **原因**: 代码中使用 `w_coefficients.values.T.flatten()` 进行转置

### 2. **a权重系数** (`a_coefficients.csv`)
```
           turbidity    ss      sd      do     ...
STZ1       0.012       0.034   0.056   0.078  ...
STZ2       0.023       0.045   0.067   0.089  ...
STZ3       0.034       0.056   0.078   0.090  ...
...
STZ25      0.098       0.076   0.054   0.032  ...
```
- **行索引**: 特征编号 (STZ1, STZ2, ..., STZ25)
- **列索引**: 水质参数 (turbidity, ss, sd, do, codmn, codcr, chla, tn, tp, chroma, nh3n)
- **原因**: 代码中使用 `a_coefficients.values.T.flatten()` 进行转置

### 3. **b幂系数** (`b_coefficients.csv`)
```
           STZ1    STZ2    STZ3    STZ4   ...  STZ25
turbidity  1.123   1.456   1.789   1.012  ...  1.987
ss         1.234   1.567   1.890   1.123  ...  1.654
sd         1.345   1.678   1.901   1.234  ...  1.321
...
nh3n       1.987   1.654   1.321   1.098  ...  1.876
```
- **行索引**: 水质参数 (turbidity, ss, sd, do, codmn, codcr, chla, tn, tp, chroma, nh3n)
- **列索引**: 特征编号 (STZ1, STZ2, ..., STZ25)
- **原因**: 代码中使用 `b_coefficients.values.flatten()` 不转置

### 4. **A微调系数** (`A_coefficients.csv`)
```
           A
turbidity  1.123
ss         1.234
sd         1.345
do         1.456
...
nh3n       1.987
```
- **行索引**: 水质参数 (turbidity, ss, sd, do, codmn, codcr, chla, tn, tp, chroma, nh3n)
- **列索引**: ["A"]
- **原因**: 代码中使用 `A_coefficients.values.flatten()` 不转置

### 5. **Range数据** (`range_data.csv`)

```
           min     max
turbidity  0.5     50.0
ss         1.0     100.0
sd         0.1     5.0
do         4.0     12.0
codmn      1.0     15.0
codcr      5.0     40.0
chla       0.1     20.0
tn         0.1     5.0
tp         0.01    0.5
chroma     5.0     50.0
nh3n       0.01    2.0
```
- **行索引**: 水质参数 (turbidity, ss, sd, do, codmn, codcr, chla, tn, tp, chroma, nh3n)
- **列索引**: ["min", "max"] (最小值和最大值)
- **数据内容**: 每个水质参数的取值范围
- **说明**: 用户直接上传min/max格式，系统内部会转换为["m", "n"]格式进行处理

## 🔄 数据处理流程

### Type 0 (微调模式)
1. 用户上传: `A_coefficients.csv`, `range_data.csv`
2. 系统处理: 
   - 直接使用A系数: `A_coefficients.values.flatten()`
   - 处理Range系数: 将["min", "max"]重命名为["m", "n"]

### Type 1 (完整建模模式)
1. 用户上传: `w_coefficients.csv`, `a_coefficients.csv`, `b_coefficients.csv`, `range_data.csv`
2. 系统处理:
   - w系数转置: `w_coefficients.values.T.flatten()`
   - a系数转置: `a_coefficients.values.T.flatten()`
   - b系数不转置: `b_coefficients.values.flatten()`
   - **自动生成A系数**: 根据Range数据的水质参数索引，全部设为1.0
   - 处理Range系数: 将["min", "max"]重命名为["m", "n"]

## 📋 水质参数列表

标准的11个水质参数:
- `turbidity` - 浊度
- `ss` - 悬浮物
- `sd` - 透明度
- `do` - 溶解氧
- `codmn` - 高锰酸盐指数
- `codcr` - 化学需氧量
- `chla` - 叶绿素a
- `tn` - 总氮
- `tp` - 总磷
- `chroma` - 色度
- `nh3n` - 氨氮

## 🏢 特征列表

标准的25个特征: STZ1, STZ2, STZ3, ..., STZ25

## ⚠️ 重要注意事项

1. **w和a系数需要转置**: 用户上传的是 特征×水质参数 格式，但系统会转置后处理
2. **b和A系数不需要转置**: 用户上传的是 水质参数×特征/A 格式
3. **Range数据格式**: 用户上传水质参数×[min,max]格式，系统重命名为[m,n]格式
4. **Type 1模式A系数自动生成**: 无需用户上传A系数文件，系统根据Range数据自动生成
5. **文件名区分大小写**: 在某些系统中需要注意 `a_coefficients.csv` 和 `A_coefficients.csv` 的区别