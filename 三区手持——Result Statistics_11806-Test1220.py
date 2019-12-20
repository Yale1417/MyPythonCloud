"""
针对不同版本的三区手持眼底图像自动标注病灶区的算法结果进行统计。
@author:By Yale_yang 
Dec. 5th 2019
"""
# 业务逻辑：
# 1. 关键的数据列：医生的诊断结果（doc）,算法判断结果（v3.4.1），筛查结果（即：基于医生的诊断结果，修改算法”doc“判断为阳性，医生诊断为阴性，但经人工审核后，图像确实存在病灶！此时将”doc“列对应的图片结果修改为阳性，其余与”doc“结果保持一致，修改后的列作为最终的筛查结果列）
# 2. 关键步骤：提取算法”doc“判断为阳性，医生诊断为阴性的图片，进行下一步人工审核；

import re
import os 
import shutil  #拷贝数据的模块
import pandas as pd 
import matplotlib.pyplot as plt
pd.set_option('display.max_columns',None)
pd.set_option('display.max_rows',None)
pd.set_option('expand_frame_repr',False)   #禁止自动换行
print('import succed!')

input_path = r'/Users/edz/Documents/My-work/Daily_work/算法结果统计/mine/导入Data'
df_template_file = r'/三区域-异常算法-指标统计-2019总表.xls'   # 统计的样表数据
df_sf = r'/result_11806_suan.csv'  # 算法每次更新的结果数据——需修改

# 文件读入
df_sf = pd.read_csv(input_path+df_sf, sep=',', index_col=None)   # 算法结果
# df_sf.drop(columns=[1,3,5,7],inplace=True)

print(df_sf.head())

df_sf.rename(columns={'image_name':'md5','health_or_not':'Arithmetic_result',
                      'optic':'item_1','macular':'item_2','retina':'item_3'},inplace=True)
print(df_sf.head())


df_sf['item_sum'] = df_sf.loc[:,['item_1','item_2','item_3']].apply(lambda x:x.sum(),axis=1)   #'item_sum'列计算'item_1','item_2','item_3'三列的总和
# 根据'item_1','item_2','item_3'中有一项结果为1，则最终的”decison_last“应该标记为”1“，来验证”decison_last“列的数据是否存在错误
for i in range(len(df_sf['md5'])):
    if df_sf.at[i,'item_sum'] > 0:
        if df_sf.at[i,'Arithmetic_result'] == 1:
            pass
        else:
            print("{} index of Arithmetic_result_阳性 is Error! ".format(i))
    else:
        if df_sf.at[i,'Arithmetic_result'] == 0:
            pass
        else:
            print("{} index of Arithmetic_result_阴性 is Error! ".format(i))


print(df_sf.head())


# 读入template_mine.xls，得到患者信息和医生的诊断结果
df_tempt = pd.read_excel(input_path+df_template_file, sheet_name='11806', sep='\t', index_col=None)

df_tempt['md5'] = df_tempt['md5'] + '.jpg'
print(df_tempt.head())
# 校验df_sf和df_tempt的数据条目总数是否相等~
if df_sf.shape[0] == df_tempt.shape[0]:
    print('df_sf和df_tempt的数据条目总数相等！')
else:
    print('df_sf数据条目为{},df_tempt数据条目为{}'.format(df_sf.shape[0],df_tempt.shape[0]))

# 合并df_sf表与tempt_mine表中的数据
df = pd.merge(df_tempt,df_sf[['md5','Arithmetic_result']],how='left',on='md5',sort=False)   #参数sort：是否根据”连接键“对合并后的数据进行排序，默认为True
# df.head() 

# # Pandas按指定条件筛选行数据
# ## 同时满足A列值为0，B列值为1的所有行数据
# df[(df['Doctor_standard']==0) & (df['Arithmetic_result']==1)]
# <br>亦或
# <br>df.loc[(df['Doctor_standard']==0) & (df['Arithmetic_result']==1),:]
# ## 业务逻辑：真假以医生的诊断结果为准，阴阳以算法的计算结果为准，二者排列组合。
# <br>真阳性(TP)：医生诊断为阳性，算法判断为阳性；
# <br>假阳性(FP)：医生诊断为阴性，算法判断为阳性；（‘误诊’）
# <br>真阴性(TN)：医生诊断为阴性，算法判断为阴性；
# <br>假阴性(FN)：医生诊断为阳性，算法判断为阴性；（‘漏诊’）


#根据指定筛选条件对算法数据进行分类
df_TP = df[(df['Doctor_standard']==1) & (df['Arithmetic_result']==1)]   # 真阳性
df_FP = df[(df['Doctor_standard']==0) & (df['Arithmetic_result']==1)]   # 假阳性——误诊
df_TN = df[(df['Doctor_standard']==0) & (df['Arithmetic_result']==0)]   # 真阴性
df_FN = df[(df['Doctor_standard']==1) & (df['Arithmetic_result']==0)]   # 假阴性——漏诊
print(df_FN.head())   #验证结果

print("{}张假阳性图片数据".format(len(df_FP))) 

output_path =  r'/Users/edz/Documents/My-work/Daily_work/算法结果统计/mine/导出Result'
output_file = r'/df_V3.4.1版本_11806.xlsx'   
writer = pd.ExcelWriter(output_path+output_file)
df_FP.to_excel(writer,sheet_name='df_FP误诊',index=None)   #  “假阳性——误诊“
df_FN.to_excel(writer,sheet_name='df_FN漏诊',index=None)    # “假阴性——漏诊”
writer.save()

# # Part02 算法“误诊”的数据由两部分组成：
# （1）图片确实存在明显病灶，尽管医生诊断患者为阴性，但算法是基于”病灶正确标注“设计的，因此算法的判断结果——正确；<br>
# （2）图片的病灶不确定，由于医生诊断患者为阴性，此时仍以医生的结果为准，认为算法的病灶标注错误，因此算法的判断结果——错误；
# 接下来，人工审核环节的主要工作就是校核找出（1）部分的”假阳性“算法数据。
# <br>筛查标准列”Screening_standard“=修改过的——医生诊断结果列”Doctor_standard“（修改”假阳性“数据中图片存在明显病灶的医生诊断结果数据为”阳性“）
# ## 根据筛选出的”假阳“图片名称，寻找对应的图片，并将其copy到指定文件夹下  

df_FP.reset_index(drop=True,inplace=True)   # 重置索引
df_FN.reset_index(drop=True,inplace=True)   # 重置索引
print(df_FP.head())

select_list_FP = []   # 定义存放df_FP图片名称的列表
for i in range(len(df_FP['md5'])):
    select_list_FP.append(df_FP.at[i,'md5'])

select_list_FN = []   # 定义存放df_FN图片名称的列表
for i in range(len(df_FN['md5'])):
    select_list_FN.append(df_FN.at[i,'md5'])    


copy_image_path_FN = r'/Users/edz/Documents/My-work/Daily_work/算法结果统计/mine/导出Result/FN_image_11806'
copy_image_path_FP = r'/Users/edz/Documents/My-work/Daily_work/算法结果统计/mine/导出Result/FP_image_11806'
Label_image_path = r'/Users/edz/Documents/My-work/Daily_work/算法结果统计/v3.4.1/11806/result_11806'
n = 0  # 统计数目
m = 0
for maindir, subdir, file_name_list in os.walk(Label_image_path):
#     print(maindir)
    for filename in file_name_list:
        if filename.endswith('.jpg' or '.JPG'):
            if filename in select_list_FP:
                olddir = os.path.join(maindir,filename)
#                 print(filename,'在目标文件夹中')
                copy_filedir_FP = os.path.join(copy_image_path_FP,filename)   # copy_filedir定义了copy_FP图片的目标文件夹
                n += 1
                shutil.copy(olddir,copy_filedir_FP)   # 执行Copy图片的操作
            elif filename in select_list_FN:
                olddir = os.path.join(maindir,filename)
#                 print(filename,'在目标文件夹中')
                copy_filedir_FN = os.path.join(copy_image_path_FN,filename)   # copy_filedir定义了copy_FN图片的目标文件夹
                m += 1
                shutil.copy(olddir,copy_filedir_FN)   # 执行Copy图片的操作
            else:
                pass

print('FP符合的文件数',n)  
print('FN符合的文件数',m)  

# ## Part03：对于”假阳性图片“：即：医生诊断为阴性，但算法标注为”有病灶（即：阳性）“
# 基于人工审核过，过滤掉”医生诊断为阴性，但图像标注确实是有病灶的图片“，其余的算作算法标注病灶错误。

# 将筛选出的中文件夹的图片文件的文件名提取出来，并且转化为”图片名称的list“
input_doctor_modified_path = r'/Users/edz/Documents/My-work/Daily_work/算法结果统计/mine/导入Data/算法正确-820'
doctor_modified_list = []
for maindir, subdir,file_name_list in os.walk(input_doctor_modified_path):
    for filename in file_name_list:
        if filename.endswith('.jpg' or '.JPG'):
            doctor_modified_list.append(filename)
print(len(doctor_modified_list),'doctor诊断结果的column中需要修改为阳性的行数据总条数！')

# 将原”Doctor_standard“列复制给”筛查标准列“，此处即：”Screening_standard“列
df.insert(df.columns.get_loc('Doctor_standard')+1,'Screening_standard',value=df['Doctor_standard'])   # 指定位置插入插入指定列，同时用指定的某列的值填充对应项
print(df.head())   #验证插入列是否符合要求

# 修改template_mine.xls中”Doctor_standard“为”0“（即：人工审核后52张医生诊段结果为阴性，但算法标注图像确实存在病灶的图片，此时将医生诊断结果”doc“列的结果修改为阳性，作为新的筛查标准）
m = 0
for i in range(len(df['md5'])):
    if df.at[i,'md5'] in doctor_modified_list:
        #print(df_template_gai.at[i,'doc'])
        df.at[i,'Screening_standard'] = 1   # 修改'Screening_standard'列
        m += 1
    else:
        pass
print('"Screening_standard"列修改——基于doctor诊断结果列”Doctor_standard“中共计{}条数据需修改为阳性（即：1）~'.format(m))    


# 直接筛选出'Doctor_standard','Screening_standard'两列值不相等的行数据的DataFrame,# 验证修改成功
a = df.loc[df['Doctor_standard'] != df['Screening_standard'],['Doctor_standard','Screening_standard']]
print(len(a))


template_last_output_path = r'/Users/edz/Documents/My-work/Daily_work/算法结果统计/mine/导出Result'
template_last_file = r'/template_last_11806.xlsx'
writer1 = pd.ExcelWriter(template_last_output_path + template_last_file)
df.to_excel(writer1,sheet_name='V3.4.1版本',index=None)
writer1.save()

# ## Part04 输出符合要求的统计表
# 基于“图片”维度和“患者”两个类别：
# <br>分别比较、统计:
# <br>(a)算法结果“Arithmetic_result”与医生诊断结果“Doctor_standard”的不同标签的样本数，以及“敏感性”、“特异性”和“准确性”；
# <br>(a)算法结果“Arithmetic_result”与筛查标准结果“Screening_standard”的不同标签的样本数，以及“敏感性”、“特异性”和“准确性”；

## (1) 图片维度
# ### “敏感性”、“特异性”和“准确性”的计算公式如下：
# <br>(1)敏感性：TP/(TP+FN)
# <br>(2)特异性：TN/(TN+FP)
# <br>(3)准确性：(TP+TN)/(TP+TN+FP+FN)

# 计算 “敏感性”、“特异性”和“准确性”
def statistics_fun(dfname_TP,dfname_FP,dfname_TN,dfname_FN):
    Sensibility = round((dfname_TP.shape[0] / (dfname_TP.shape[0] + dfname_FN.shape[0])),4)
    Specificity = round((dfname_TN.shape[0] / (dfname_TN.shape[0] + dfname_FP.shape[0])),4)
    Accuracy = round(((dfname_TP.shape[0] + dfname_TN.shape[0]) / (dfname_TP.shape[0]+dfname_FP.shape[0] + dfname_TN.shape[0] + dfname_FN.shape[0])),4)
    print("Sensibility:{}, Specificity:{}, Accuracy:{}".format(Sensibility, Specificity, Accuracy))
    return Sensibility, Specificity, Accuracy



def classification_stantistics_fun(df_item):
    #根据指定筛选条件对算法数据进行分类——诊断标准
    df_item_TP = df_item[(df_item['Doctor_standard']==1) & (df_item['Arithmetic_result']==1)]   # 真阳性
    df_item_FP = df_item[(df_item['Doctor_standard']==0) & (df_item['Arithmetic_result']==1)]   # 假阳性——误诊
    df_item_TN = df_item[(df_item['Doctor_standard']==0) & (df_item['Arithmetic_result']==0)]   # 真阴性
    df_item_FN = df_item[(df_item['Doctor_standard']==1) & (df_item['Arithmetic_result']==0)]   # 假阴性——漏诊
    print("诊断标准：")
    print("TP:{}, FP:{}, TN:{}, FN:{}".format(df_item_TP.shape[0],df_item_FP.shape[0],df_item_TN.shape[0],df_item_FN.shape[0]))   #验证结果
    
    Sensibility = round((df_item_TP.shape[0] / (df_item_TP.shape[0] + df_item_FN.shape[0])),4)
    Specificity = round((df_item_TN.shape[0] / (df_item_TN.shape[0] + df_item_FP.shape[0])),4)
    Accuracy = round(((df_item_TP.shape[0] + df_item_TN.shape[0]) / (df_item_TP.shape[0]+df_item_FP.shape[0] + df_item_TN.shape[0] + df_item_FN.shape[0])),4)
    print("Sensibility:{}, Specificity:{}, Accuracy:{}".format(Sensibility, Specificity, Accuracy))
#     return Sensibility, Specificity, Accuracy
    #     statistics_fun(df_item_TP,df_item_FP,df_item_TN,df_item_FN)   # 调用函数——计算Sensibility, Specificity, Accuracy
    
    #根据指定筛选条件对算法数据进行分类——筛查标准
    df_item_sc_TP = df_item[(df_item['Screening_standard']==1) & (df_item['Arithmetic_result']==1)]   # 真阳性
    df_item_sc_FP = df_item[(df_item['Screening_standard']==0) & (df_item['Arithmetic_result']==1)]   # 假阳性——误诊
    df_item_sc_TN = df_item[(df_item['Screening_standard']==0) & (df_item['Arithmetic_result']==0)]   # 真阴性
    df_item_sc_FN = df_item[(df_item['Screening_standard']==1) & (df_item['Arithmetic_result']==0)]   # 假阴性——漏诊
    print("筛查标准：")
    print("TP:{}, FP:{}, TN:{}, FN:{}".format(df_item_sc_TP.shape[0],df_item_sc_FP.shape[0],
                                              df_item_sc_TN.shape[0],df_item_sc_FN.shape[0]))   #验证结果
    
    Sensibility_sc = round((df_item_sc_TP.shape[0] / (df_item_sc_TP.shape[0] + df_item_sc_FN.shape[0])),4)
    Specificity_sc = round((df_item_sc_TN.shape[0] / (df_item_sc_TN.shape[0] + df_item_sc_FP.shape[0])),4)
    Accuracy_sc = round(((df_item_sc_TP.shape[0] + df_item_sc_TN.shape[0]) / (df_item_sc_TP.shape[0]+
                        df_item_sc_FP.shape[0] + df_item_sc_TN.shape[0] + df_item_sc_FN.shape[0])),4)
    print("Sensibility:{}, Specificity:{}, Accuracy:{}".format(Sensibility_sc, Specificity_sc, Accuracy_sc))
#     return Sensibility_sc, Specificity_sc, Accuracy_sc
#     statistics_fun(df_item_sc_TP,df_item_sc_FP,df_item_sc_TN,df_item_sc_FN)   # 调用函数——计算Sensibility, Specificity, Accuracy
    
#     return df_item_TP,df_item_FP,df_item_TN,df_item_FN,df_item_sc_TP,df_item_sc_FP,df_item_sc_TN,df_item_sc_FN
    
    global Table_item  #定义全局变量，局部变量在函数调用结束即释放，因此无法后续调用！！！
    Table_item = pd.DataFrame(columns=['属性_class','诊断标准_count','筛查标准_count'])
    Table_item['属性_class'] = ['TP','FP','TN','FN','敏感性','特异性','准确性']   # 填充“属性_class”
    Table_item['诊断标准_count'] = [df_item_TP.shape[0],df_item_FP.shape[0],df_item_TN.shape[0],df_item_FN.shape[0],
                                   str(Sensibility), str(Specificity), str(Accuracy)]
    Table_item['筛查标准_count'] = [df_item_sc_TP.shape[0],df_item_sc_FP.shape[0],df_item_sc_TN.shape[0],
                                   df_item_sc_FN.shape[0],str(Sensibility_sc), str(Specificity_sc), str(Accuracy_sc)]
    
    return Table_item



print('V3.4.1——图片维度(图片共计：{}张)'.format(df.shape[0]))
Table_image = classification_stantistics_fun(df)

template_last_output_path = r'/Users/edz/Documents/My-work/Daily_work/算法结果统计/mine/导出Result/template_last_excel'
template_last_file = r'/template_last_11806_V3.4.1版本.xlsx'
writer1 = pd.ExcelWriter(template_last_output_path + template_last_file)
Table_image.to_excel(writer1,sheet_name='V3.4.1版本_图片维度_分表',index=None)
writer1.save()

## 患者标准

# 调试——列名不一致问题
print(df.columns)
if '姓名' in df.columnsolumns
df.rename(columns={'姓名':'name'},inplace=True)


df_patient = df[['name','Doctor_standard','Screening_standard','Arithmetic_result']].groupby(by=df['name'],sort=False).sum()
print(df_patient.head())

# 获取Doctor_standard、Screening_standard和Arithmetic_result的3列的value_counts()为组合情形的列表
different_index_list_a = df_patient['Doctor_standard'].value_counts().index.tolist() # 获取同一患者拍摄多张图片的可能的取值情况的列表,.reset_index() # 将索引列index转为普通列
different_index_list_b = df_patient['Screening_standard'].value_counts().index.tolist() 
different_index_list_c = df_patient['Arithmetic_result'].value_counts().index.tolist() 
# 合并列表
different_index_list = list(set(different_index_list_a+different_index_list_b+different_index_list_c))
print(different_index_list) 

#替换>1的项的值为1，其余不变~
df_patient['Screening_standard'].replace(2, 1 ,inplace=True)
for i in range(len(different_index_list)):
    if (different_index_list[i] == 0) or (different_index_list[i] == 1):
        pass
    else:
        df_patient['Doctor_standard'].replace(different_index_list[i], 1 ,inplace=True)  #替换>1的项的值为1，其余不变~
        df_patient['Screening_standard'].replace(different_index_list[i], 1 ,inplace=True)
        df_patient['Arithmetic_result'].replace(different_index_list[i], 1 ,inplace=True)


# 验证替换成功
print(df_patient['Doctor_standard'].value_counts())
print(df_patient['Screening_standard'].value_counts())
print(df_patient['Arithmetic_result'].value_counts())

print('V3.4.1——患者维度：(患者共计：{}人)'.format(df_patient.shape[0]))
Table_patient = classification_stantistics_fun(df_patient)
print(Table_patient)

#校验以"患者"维度分段聚合后，图片数量和患者数量的总数保持一致
patient_items = 0   # 初始化为0
for i in range(4):
    print(type(int(Table_patient.at[i,'诊断标准_count'])))    # 将字符型转为int型，后续累加TP、FP、TN、FN各项的累加和是否为“患者”总人数
    patient_items += Table_patient.at[i,'诊断标准_count']
if patient_items==df_patient.shape[0]:
    print("患者维度：TP、FP、TN、FN各项的累加之和：{}~与患者总人数一致！".format(patient_items))
else:
    print("ERROR:患者维度：TP、FP、TN、FN各项的累加之和与患者总人数相差{}人".format(df_patient.shape[0] - patient_items))


templathie_last_output_path = r'/Users/edz/Documents/My-work/Daily_work/算法结果统计/mine/导出Result/template_last_excel'
template_last_file = r'/template_last_11806_V3.4.1版本_分表.xlsx'
writer2 = pd.ExcelWriter(template_last_output_path + template_last_file)
Table_image.to_excel(writer2,sheet_name='V3.4.1版本_图片维度_分表',index=None)
Table_patient.to_excel(writer2,sheet_name='V3.4.1版本_患者维度',index=None)
writer2.save()




















