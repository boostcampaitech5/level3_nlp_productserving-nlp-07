import { HeaderLogoBlock } from "@blocks/HeaderLogo";
import { useEffect, useState } from "react";
import styled, { css } from "styled-components";
import check from "@assets/images/check.png";
import * as KF from "@styles/keyframes";
import axios from "axios";
import { DBDataType } from "@apis/DB_api";
import Spinner from "@blocks/Spinner";

interface ProgressType {
  progress: number;
}

interface LoadingType {
  isdone: number;
}

const ResultPage = () => {
  const [curProgress, setProgress] = useState(0);
  const [isLoaded, setLoaded] = useState(false);
  const [showResult, setResult] = useState(false);
  const [db_data, setData] = useState<DBDataType | null>(null);
  const [db_loaded, setDBLoaded] = useState(false);
  const [retrieve_loaded, setRetrieveLoaded] = useState(false);
  // const [retrieve_result, setRetrieveResult] = useState("");
  const [summary_loaded, setSummaryLoaded] = useState(false);
  const [summary_result, setSummaryResult] = useState("");

  var product = localStorage.getItem("itemName");
  var query = localStorage.getItem("itemOption");

  useEffect(() => {
    const FetchData = async () => {
      await axios({
        method: "get",
        url: "/api/reviews/search/prod_name/" + product,
      }).then((response) => {
        setData(response.data);
        setDBLoaded(true);
        axios({
          method: "post",
          url: process.env.REACT_APP_DPR_ENDPOINT + "/dpr/split_db",
          headers: {
            Accept: "*/*",
            "Content-Type": "application/json",
          },
          data: {
            query: query,
            reviews: response.data.reviews,
          },
        }).then((dpr_response) => {
          setRetrieveLoaded(true);
          axios({
            method: "post",
            url: process.env.REACT_APP_SUMMARY_ENDPOINT + "/summary",
            headers: {
              Accept: "*/*",
              "Content-Type": "application/json",
            },
            data: [dpr_response.data.review],
          }).then((summary_response) => {
            setSummaryResult(summary_response.data);
            setSummaryLoaded(true);
            setTimeout(() => setLoaded(true), 2000);
            setTimeout(() => setResult(true), 6200);
          });
        });
      });
    };
    FetchData();

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // useEffect(()=>{
  //   // setTimeout(() => {
  //   //   for (let i = 0; i <= 100; i += 1) {
  //   //     setTimeout(() => setProgress(curProgress + i), 50 * i);
  //   //   }
  //   // }, 1400);
  // })

  if (curProgress === 100) {
    setTimeout(() => setLoaded(true), 2000);
    setTimeout(() => setResult(true), 6200);
  }

  if (!showResult && !isLoaded) {
    return (
      <>
        <HeaderLogoBlock />
        <CenterWrapper>
          <LodingDiv isdone={summary_loaded ? 1 : 0}>
            <LodingText>
              {!db_loaded
                ? "리뷰 데이터를 수집하고 있어요"
                : !retrieve_loaded
                ? "리뷰 데이터를 분석하고 있어요"
                : "리뷰 데이터를 요약하고 있어요"}
            </LodingText>
            <Spinner />
          </LodingDiv>
          {/* <LodingCenterText progress={curProgress}>
            상품을 찾고 있어요.
          </LodingCenterText>
          <ProgressBarDiv progress={curProgress}>
            <ProgressBar progress={curProgress} />
            <ProgressText>{curProgress}%</ProgressText>
          </ProgressBarDiv> */}
        </CenterWrapper>
      </>
    );
  }
  if (!showResult && isLoaded) {
    return (
      <>
        <HeaderLogoBlock />
        <CenterWrapper>
          <CenterText>조건에 맞는 상품을 찾았어요!</CenterText>
          <CheckImg src={check} alt="" />
        </CenterWrapper>
      </>
    );
  }

  return (
    <>
      <HeaderLogoBlock />
      <ItemDiv></ItemDiv>
      <TextDiv>
        <Description>
          원하시는 조건에 맞는 상품을 찾아왔어요.
          <br />
          상품에 대한 리뷰 요약도 보여드릴게요.
          <br />
          <br />
          {/* 원하시는 조건에 맞는 상품을 찾아왔어요.
        <br />위 상품은 이렇고, 저렇습니다. (상품 설명 요약) */}
          {summary_result}
          {/* &lt;맛&gt; 맛있어요 &lt;양&gt; 30개씩 주문하면 너무 많고 10개씩
          주문하면 한 달 먹기 딱 좋아요 &lt;조리&gt; 날 계란을 넣어 주시고
          수프를 넣어 주세요 &lt;맛&gt; 면도 부드럽고 국물도 더욱 구수해집니다
          &lt;추천&gt; 추운 겨울 백제 쌀국수로 따뜻하고 시원하게 즐겨보세요
          &lt;맛&gt; 달달하고 계속 당기는 그 맛 &lt;양&gt; 성인 두 분이 드시기에
          딱 좋은 양 &lt;조리&gt; 물 또는 보리차 넣어서 끓이라고 써있는데
          떡본연의 맛 때문에 그런것인가 &lt;선호&gt; 아이가 어려서 많이
          매워한다면 체다치즈 한장 넣으면 매운게 훨씬 덜 함 &lt;향&gt; 추억의
          국물떡볶이 */}
        </Description>
      </TextDiv>
    </>
  );
};

export default ResultPage;

const CenterWrapper = styled.div`
  margin: 0 auto;
  margin-top: 230rem;
  width: 700rem;
  height: 274rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
`;

const LodingCenterText = styled.span<ProgressType>`
  color: #4a4a4a;
  text-align: center;
  font-size: 36rem;
  font-family: Pretendard;
  font-style: normal;
  font-weight: 700;
  line-height: normal;

  ${css`
    animation: ${KF.start} 0.8s 0.2s 1 both;
  `}

  ${(props) =>
    props.progress === 100 &&
    css`
      animation: ${KF.end} 0.8s 1.2s 1 both;
    `}
`;

const CenterText = styled.span`
  color: #4a4a4a;
  text-align: center;
  font-size: 36rem;
  font-family: Pretendard;
  font-style: normal;
  font-weight: 700;
  line-height: normal;

  ${css`
    animation: ${KF.startEnd} 4s 0s 1 both;
  `}
`;

const ProgressBarDiv = styled.div<ProgressType>`
  width: 700rem;
  height: 74rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;

  ${css`
    animation: ${KF.start} 0.8s 0.6s 1 both;
  `}

  ${(props) =>
    props.progress === 100 &&
    css`
      animation: ${KF.end} 0.8s 1s 1 both;
    `}
`;

const ProgressBar = styled.div<ProgressType>`
  width: 700rem;
  height: 30rem;
  background: linear-gradient(
    90deg,
    #4b81bf ${(props) => props.progress}%,
    #ffffff ${(props) => props.progress}%
  );

  border-radius: 20rem;
  box-shadow: 0rem 0rem 17rem 0rem rgba(0, 0, 0, 0.25);
`;

const ProgressText = styled.span`
  color: #4a4a4a;
  text-align: center;
  font-size: 25rem;
  font-family: Pretendard;
  font-style: normal;
  font-weight: 600;
  line-height: normal;
`;

const CheckImg = styled.img`
  width: 100rem;
  height: 100rem;
  margin: 0 auto;
  margin-top: 110rem;

  animation: ${KF.startEnd} 4s 0.2s 1 both;
`;

const ItemDiv = styled.div`
  margin: 0 auto;
  margin-top: 90rem;
  margin-bottom: 50rem;
  width: 417rem;
  height: 539rem;
  flex-shrink: 0;
  border-radius: 20rem;
  background: #fff;
  box-shadow: 0rem 0rem 17rem 0rem rgba(0, 0, 0, 0.25);

  ${css`
    animation: ${KF.start2} 0.8s 0.2s 1 both;
  `}
`;

const Description = styled.span`
  margin: 0 auto;
  color: #4a4a4a;
  text-align: center;
  font-size: 28rem;
  font-family: Pretendard;
  font-style: normal;
  font-weight: 500;
  line-height: 150%;
  width: 200rem;
  ${css`
    animation: ${KF.start} 0.8s 0.4s 1 both;
  `};
`;

const LodingText = styled.span`
  color: #4a4a4a;
  text-align: center;
  font-size: 36rem;
  font-family: Pretendard;
  font-style: normal;
  font-weight: 700;
  line-height: normal;
`;

const LodingDiv = styled.div<LoadingType>`
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: center;
  height: 200rem;
  ${css`
    animation: ${KF.start} 0.8s 0.6s 1 both;
  `}

  ${(props) =>
    props.isdone === 1 &&
    css`
      animation: ${KF.end} 0.8s 1s 1 both;
    `}
`;

const TextDiv = styled.div`
  width: 90vw;
  margin: 0 auto;
`;
