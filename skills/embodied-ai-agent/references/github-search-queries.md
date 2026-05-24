# GitHub Search Queries

这份查询模板参考 `github-trending` skill，给 `Multi-Source-Research-Agent` 的 GitHub 链路提供可复用的基础检索语句。

## 通用查询

```text
q={keyword}&sort=stars&order=desc&per_page=8
q={keyword}&sort=updated&order=desc&per_page=8
```

## World Model

```text
q=world+model&sort=stars&order=desc&per_page=8
q=world-model+robotics&sort=stars&order=desc&per_page=8
q=world+model+driving&sort=stars&order=desc&per_page=8
q=dreamer+dreamerv3&sort=stars&order=desc&per_page=8
```

## World Action Model

```text
q=world+action+model&sort=stars&order=desc&per_page=8
q=world-action-model+robotics&sort=stars&order=desc&per_page=8
q=action+conditioned+world+model&sort=stars&order=desc&per_page=8
```

## VLA / Embodied AI

```text
q=vision+language+action+robot&sort=stars&order=desc&per_page=8
q=openvla+pi0+rt-2&sort=stars&order=desc&per_page=8
q=robot+foundation+model&sort=stars&order=desc&per_page=8
```

## 说明

- 无鉴权 GitHub API 默认每小时 60 次请求。
- 若命中 rate limit，需要退回到网页检索或稍后重试。
- 关键词进入流水线前，建议先做一次候选筛选，再选择代表性仓库生成 Wiki 草稿。
